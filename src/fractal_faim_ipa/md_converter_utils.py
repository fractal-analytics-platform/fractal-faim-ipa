"""MD Converter utils."""
from enum import Enum

from faim_ipa.hcs.imagexpress import (
    MixedAcquisition,
    SinglePlaneAcquisition,
    StackAcquisition,
)

import fractal_faim_ipa


class ModeEnum(Enum):
    """Handle selection of conversion mode."""

    StackAcquisition = "MD Stack Acquisition"
    SinglePlaneAcquisition = "MD Single Plane Acquisition"
    MixedAcquisition = "MD MixedAcquisition"
    ZMBStackAcquisition = "ZMB MD Stack Acquisition"

    def get_plate_acquisition(self, acquisition_dir, alignment):
        """Run acquisition function for chosen mode."""
        if self == ModeEnum.StackAcquisition:
            return StackAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.SinglePlaneAcquisition:
            return SinglePlaneAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.MixedAcquisition:
            return MixedAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.ZMBStackAcquisition:
            return fractal_faim_ipa.StackAcquisition(acquisition_dir, alignment)
        else:
            raise NotImplementedError(f"MD Converter was not implemented for {self=}")
