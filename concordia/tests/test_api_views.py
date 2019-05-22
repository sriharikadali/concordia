from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from concordia.models import Asset, Item, Transcription, TranscriptionStatus, User
from concordia.utils import get_anonymous_user

from .utils import JSONAssertMixin, create_asset, create_item, create_project


@override_settings(RATELIMIT_ENABLE=False)
class ConcordiaViewTests(JSONAssertMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anon_user = get_anonymous_user()

        cls.reviewer = User.objects.create_user(
            username="reviewer", email="tester@example.com"
        )

        project = create_project()

        cls.items = [
            create_item(
                item_id=f"item_{i}", title=f"Item {i}", project=project, do_save=False
            )
            for i in range(0, 3)
        ]
        Item.objects.bulk_create(cls.items)

        cls.assets = []
        for item in cls.items:
            for i in range(0, 15):
                cls.assets.append(
                    create_asset(title=f"{item.id} — {i}", item=item, do_save=False)
                )
        Asset.objects.bulk_create(cls.assets)

        cls.transcriptions = []
        for asset in cls.assets:
            last_t = None

            for n in range(0, 3):
                cls.transcriptions.append(
                    Transcription(
                        asset=asset,
                        supersedes=last_t,
                        text=f"{asset} — {n}",
                        user=cls.anon_user,
                    )
                )

        Transcription.objects.bulk_create(cls.transcriptions)

        submitted_t = cls.transcriptions[-1]
        submitted_t.submitted = now()
        submitted_t.full_clean()
        submitted_t.save()

    def get_asset_list(self, url, page_size=23):
        resp = self.client.get(url, {"per_page": page_size})
        data = self.assertValidJSON(resp)

        self.assertIn("objects", data)
        object_count = len(data["objects"])
        self.assertLessEqual(object_count, 23)

        self.assertIn("pagination", data)

        self.assertAssetsHaveLatestTranscriptions(data["objects"])

        return resp, data

    def assertAssetStatuses(self, asset_list, expected_statuses):
        asset_pks = [i["id"] for i in asset_list]

        self.assertQuerysetEqual(
            Asset.objects.filter(pk__in=asset_pks).exclude(
                transcription_status__in=expected_statuses
            ),
            [],
        )

    def assertAssetsHaveLatestTranscriptions(self, asset_list):
        asset_pks = {i["id"]: i for i in asset_list}

        for asset in Asset.objects.filter(pk__in=asset_pks.keys()):
            latest_trans = asset.transcription_set.latest("pk")

            if latest_trans is None:
                self.assertIsNone(asset_pks[asset.id]["latest_transcription"])
            else:
                self.assertDictEqual(
                    asset_pks[asset.id]["latest_transcription"],
                    {
                        "id": latest_trans.pk,
                        "text": latest_trans.text,
                        "submitted_by": latest_trans.user_id,
                    },
                )

    def test_asset_list(self):
        resp, data = self.get_asset_list(reverse("assets-list-json"))

    def test_transcribable_asset_list(self):
        resp, data = self.get_asset_list(reverse("transcribe-assets-json"))

        self.assertAssetStatuses(
            data["objects"],
            [TranscriptionStatus.NOT_STARTED, TranscriptionStatus.IN_PROGRESS],
        )

    def test_reviewable_asset_list(self):
        resp, data = self.get_asset_list(reverse("review-assets-json"))

        self.assertAssetStatuses(data["objects"], [TranscriptionStatus.SUBMITTED])

        self.assertGreater(len(data["objects"]), 0)