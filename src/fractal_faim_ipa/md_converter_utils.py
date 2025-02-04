"""MD Converter utils."""
from enum import Enum

from faim_ipa.hcs.imagexpress import (
    MixedAcquisition,
    SinglePlaneAcquisition,
    StackAcquisition,
)


class ModeEnum(Enum):
    """Handle selection of conversion mode."""

    StackAcquisition = "Stack Acquisition"
    SinglePlaneAcquisition = "Single Plane Acquisition"
    MixedAcquisition = "Mixed Acquisition"

    def get_plate_acquisition(self, acquisition_dir, alignment, query=None):
        """Run acquisition function for chosen mode."""
        if self == ModeEnum.StackAcquisition:
            return StackAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.SinglePlaneAcquisition:
            return SinglePlaneAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.MixedAcquisition:
            return MixedAcquisition(acquisition_dir, alignment)
        else:
            raise NotImplementedError(f"MD Converter was not implemented for {self=}")
