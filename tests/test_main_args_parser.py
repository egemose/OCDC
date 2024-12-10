import pathlib
import unittest

import numpy as np
import pytest

from OCDC.__main__ import parse_args, process_color_model_args, process_transform_args
from OCDC.color_models import GaussianMixtureModelDistance, MahalanobisDistance, ReferencePixels
from OCDC.transforms import GammaTransform, LambdaTransform

test_reference_pixels_values = np.array([[5, 20, 99], [5, 20, 100], [5, 19, 101]])


class TestArgsParser(unittest.TestCase):
    def test_required_and_default_args(self):
        parser = parse_args(["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png"])
        # test required args
        assert parser.orthomosaic == pathlib.Path("/test/home/ortho.tiff")
        assert parser.reference == pathlib.Path("/test/home/ref.tiff")
        assert parser.annotated == pathlib.Path("/test/home/anno.png")
        # test default args
        assert parser.bands_to_use is None
        assert parser.alpha_channel == -1
        assert parser.scale == 5
        assert parser.output_tile_location == pathlib.Path("output/tiles")
        assert parser.mask_file_name == pathlib.Path("pixel_values")
        assert parser.method == "mahalanobis"
        assert parser.param == 2
        assert parser.tile_size == 3000
        assert parser.run_specific_tile is None
        assert parser.run_specific_tileset is None
        assert parser.gamma_transform is None
        assert parser.lambda_transform is None
        # test missing required args
        with pytest.raises(SystemExit):
            parse_args(["/test/home/ortho.tiff", "/test/home/ref.tiff"])
        with pytest.raises(SystemExit):
            parse_args([])

    def test_optional_args_with_different_values(self):
        # test all other arguments
        parser = parse_args(
            [
                "/test/home/ortho.tiff",
                "/test/home/ref.tiff",
                "/test/home/anno.png",
                "--bands_to_use",
                "0",
                "1",
                "2",
                "--alpha_channel",
                "4",
                "--scale",
                "2",
                "--output_tile_location",
                "/test/home/output",
                "--mask_file_name",
                "/test/home/mask_pixels",
                "--method",
                "gmm",
                "--param",
                "5",
                "--tile_size",
                "1000",
                "--run_specific_tile",
                "16",
                "65",
                "--run_specific_tileset",
                "16",
                "65",
                "--gamma_transform",
                "0.5",
                "--lambda_transform",
                "lambda x: x+5",
            ]
        )
        assert parser.bands_to_use == [0, 1, 2]
        assert parser.alpha_channel == 4
        assert parser.scale == 2
        assert parser.output_tile_location == pathlib.Path("/test/home/output")
        assert parser.mask_file_name == pathlib.Path("/test/home/mask_pixels")
        assert parser.method == "gmm"
        assert parser.param == 5
        assert parser.tile_size == 1000
        assert parser.run_specific_tile == [16, 65]
        assert parser.run_specific_tileset == [16, 65]
        assert parser.gamma_transform == 0.5
        assert parser.lambda_transform == "lambda x: x+5"


class TestArgParserTransforms(unittest.TestCase):
    def test_transform_args(self):
        args = parse_args(
            ["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png", "--gamma_transform", "0.5"]
        )
        transform_args = process_transform_args(args)
        assert isinstance(transform_args["transform"], GammaTransform)
        assert transform_args["transform"].gamma == 0.5
        args = parse_args(
            [
                "/test/home/ortho.tiff",
                "/test/home/ref.tiff",
                "/test/home/anno.png",
                "--lambda_transform",
                "lambda x: x+5",
            ]
        )
        transform_args = process_transform_args(args)
        assert isinstance(transform_args["transform"], LambdaTransform)
        args = parse_args(["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png"])
        transform_args = process_transform_args(args)
        assert transform_args["transform"] is None


class TestArgParserColorModels(unittest.TestCase):
    def setUp(self):
        self.monkeypatch = pytest.MonkeyPatch()

    def test_color_model_args(self):
        def mock_reference_pixels_init(self, bands_to_use, *args, **kwargs):
            self.bands_to_use = bands_to_use
            self.values = test_reference_pixels_values
            self.transform = None

        args = parse_args(
            ["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png", "--method", "mahalanobis"]
        )
        with self.monkeypatch.context() as mp:
            mp.setattr(ReferencePixels, "__init__", mock_reference_pixels_init)
            color_model = process_color_model_args(args, vars(args), save_pixels_values=False)
            assert isinstance(color_model, MahalanobisDistance)
            args = parse_args(
                ["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png", "--method", "gmm"]
            )
            color_model = process_color_model_args(args, vars(args), save_pixels_values=False)
            assert isinstance(color_model, GaussianMixtureModelDistance)
            args = parse_args(
                ["/test/home/ortho.tiff", "/test/home/ref.tiff", "/test/home/anno.png", "--method", "test_wrong"]
            )
            with pytest.raises(ValueError, match=r"Method must be one of 'mahalanobis' or 'gmm', but got (.*)"):
                color_model = process_color_model_args(args, vars(args))