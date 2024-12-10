import pathlib
import unittest

import numpy as np
import pytest

from OCDC.color_models import GaussianMixtureModelDistance, MahalanobisDistance, ReferencePixels

test_reference_pixel_image = np.astype(
    np.arange(0, 3 * 20 * 20, 1).reshape((3, 20, 20)) / (3 * 20 * 20) * 255, np.uint8
)
test_mask = np.astype(np.arange(0, 20 * 20, 1).reshape((1, 20, 20)) / (20 * 20) * 255, np.uint8)
test_bw_mask = np.where(test_mask > 100, 0, 255)
test_red_mask = test_reference_pixel_image
test_red_mask[0, :, :] = np.where(test_mask % 2 == 0, test_red_mask[0, :, :], 255)
test_red_mask[1, :, :] = np.where(test_mask % 2 == 0, test_red_mask[0, :, :], 0)
test_red_mask[2, :, :] = np.where(test_mask % 2 == 0, test_red_mask[0, :, :], 0)
test_wrong_size_mask = np.array([test_bw_mask, test_bw_mask])
test_too_small_mask = np.where(test_mask > 2, 0, 255)
test_image = np.array(
    [
        [[100, 50, 30], [30, 10, 70], [50, 45, 0]],
        [[50, 0, 0], [5, 20, 100], [60, 70, 60]],
        [[20, 30, 80], [50, 70, 10], [60, 80, 40]],
    ]
)
test_reference_pixels_values = np.array([[5, 20, 99], [5, 20, 100], [5, 19, 101]])
test_mahal_res = np.array(
    [
        [
            [61938065.050973, 72271206.423611, 54644082.905849],
            [41636481.413178, 4072473.365251, 55373481.120433],
            [12703685.569828, 30817074.564124, 83212179.641626],
        ]
    ]
)
test_gmm_1_res = np.array(
    [
        [
            [21646.328248, 25257.42584, 19097.247623],
            [14551.219067, 1425.097135, 19352.218935],
            [4439.704449, 10770.032736, 29081.097011],
        ]
    ]
)
test_gmm_2_res = np.array(
    [
        [
            [38825.142373, 25277.867819, 41555.941951],
            [23307.657938, 33230.944733, 43765.753982],
            [7013.36822, 19791.385844, 30779.979503],
        ]
    ]
)


class TestReferencePixels(unittest.TestCase):
    def setUp(self):
        self.monkeypatch = pytest.MonkeyPatch()

    def test_reference_pixels(self):
        def mock_load_reference_image(self, *args, **kwargs):
            self.reference_image = test_reference_pixel_image

        def get_mock_load_mask(mask_to_use_as_mock):
            def mock_load_mask(self, *args, **kwargs):
                self.mask = mask_to_use_as_mock

            return mock_load_mask

        with self.monkeypatch.context() as mp:
            mp.setattr(ReferencePixels, "load_reference_image", mock_load_reference_image)
            # test mask with red annotations
            mp.setattr(ReferencePixels, "load_mask", get_mock_load_mask(test_red_mask))
            ReferencePixels(
                reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=(0, 1, 2), transform=None
            )
            # test bands_to_use is set correct and matches image
            rp_none_alpha_none = ReferencePixels(
                reference=pathlib.Path("test"),
                annotated=pathlib.Path("test"),
                bands_to_use=None,
                alpha_channel=None,
                transform=None,
            )
            assert rp_none_alpha_none.bands_to_use == (0, 1, 2)
            rp_01 = ReferencePixels(
                reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=(0, 1), transform=None
            )
            assert rp_01.bands_to_use == (0, 1)
            rp_01_alpha_neg1 = ReferencePixels(
                reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=None, transform=None
            )
            assert rp_01_alpha_neg1.bands_to_use == (0, 1)
            rp_02_alpha_1 = ReferencePixels(
                reference=pathlib.Path("test"),
                annotated=pathlib.Path("test"),
                bands_to_use=None,
                alpha_channel=1,
                transform=None,
            )
            assert rp_02_alpha_1.bands_to_use == (0, 2)
            # test alpha channel an bands_to_use raises exceptions if out of bounds
            with pytest.raises(ValueError, match=r"Bands have to be between 0 and \d+, but got -?\d+\."):
                ReferencePixels(
                    reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=[-1], transform=None
                )
            with pytest.raises(ValueError, match=r"Bands have to be between 0 and \d+, but got -?\d+\."):
                ReferencePixels(
                    reference=pathlib.Path("test"),
                    annotated=pathlib.Path("test"),
                    bands_to_use=[0, 2, 8],
                    transform=None,
                )
            with pytest.raises(ValueError, match=r"Alpha channel have to be between -1 and \d+, but got -?\d+\."):
                ReferencePixels(
                    reference=pathlib.Path("test"),
                    annotated=pathlib.Path("test"),
                    bands_to_use=None,
                    alpha_channel=-2,
                    transform=None,
                )
            with pytest.raises(ValueError, match=r"Alpha channel have to be between -1 and \d+, but got -?\d+\."):
                ReferencePixels(
                    reference=pathlib.Path("test"),
                    annotated=pathlib.Path("test"),
                    bands_to_use=None,
                    alpha_channel=8,
                    transform=None,
                )
            # test black and white mask
            mp.setattr(ReferencePixels, "load_mask", get_mock_load_mask(test_bw_mask))
            ReferencePixels(
                reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=None, transform=None
            )
            # test mask of the wrong type
            mp.setattr(ReferencePixels, "load_mask", get_mock_load_mask(test_wrong_size_mask))
            with pytest.raises(TypeError):
                ReferencePixels(
                    reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=None, transform=None
                )
            # test mask which selects to few pixels
            mp.setattr(ReferencePixels, "load_mask", get_mock_load_mask(test_too_small_mask))
            with pytest.raises(Exception, match=r"Not enough annotated pixels. Need at least \d+, but got \d+"):
                ReferencePixels(
                    reference=pathlib.Path("test"), annotated=pathlib.Path("test"), bands_to_use=None, transform=None
                )


class TestColorModels(unittest.TestCase):
    def setUp(self):
        self.monkeypatch = pytest.MonkeyPatch()

    def test_calculate_distance(self):
        def mock_reference_pixels_init(self, bands_to_use, *args, **kwargs):
            self.bands_to_use = bands_to_use
            self.values = test_reference_pixels_values
            self.transform = None

        with self.monkeypatch.context() as mp:
            mp.setattr(ReferencePixels, "__init__", mock_reference_pixels_init)
            # test Mahalanobis distance calculations
            md = MahalanobisDistance(bands_to_use=[0, 1, 2])
            np.testing.assert_almost_equal(md.calculate_distance(test_image), test_mahal_res, decimal=6)
            # test Gaussian Mixture Model distance calculations with 1 cluster
            gmmd1 = GaussianMixtureModelDistance(bands_to_use=[0, 1, 2], n_components=1)
            np.testing.assert_almost_equal(gmmd1.calculate_distance(test_image), test_gmm_1_res, decimal=6)
            # test Gaussian Mixture Model distance calculations with 2 cluster
            gmmd2 = GaussianMixtureModelDistance(bands_to_use=[0, 1, 2], n_components=2)
            np.testing.assert_almost_equal(gmmd2.calculate_distance(test_image), test_gmm_2_res, decimal=6)