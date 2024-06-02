"""MD Converter utils."""
from enum import Enum

from faim_ipa.hcs.imagexpress import (
    MixedAcquisition,
    SinglePlaneAcquisition,
    StackAcquisition,
)

import fractal_faim_ipa
import fractal_faim_ipa.imagexpress_zmb


class ModeEnum(Enum):
    """Handle selection of conversion mode."""

    StackAcquisition = "MD Stack Acquisition"
    SinglePlaneAcquisition = "MD Single Plane Acquisition"
    MixedAcquisition = "MD Mixed Acquisition"
    MetaXpressStackAcquisition = "MetaXpress MD Stack Acquisition"
    MetaXpressSinglePlaneAcquisition = "MetaXpress MD Single Plane Acquisition"
    MetaXpressSinglePlaneAcquisition_as3D = (
        "MetaXpress MD Single Plane Acquisition as 3D"
    )
    MetaXpressMixedAcquisition = "MetaXpress MD Mixed Acquisition"

    def get_plate_acquisition(self, acquisition_dir, alignment, query=None):
        """Run acquisition function for chosen mode."""
        if self == ModeEnum.StackAcquisition:
            return StackAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.SinglePlaneAcquisition:
            return SinglePlaneAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.MixedAcquisition:
            return MixedAcquisition(acquisition_dir, alignment)
        elif self == ModeEnum.MetaXpressStackAcquisition:
            return fractal_faim_ipa.imagexpress_zmb.StackAcquisition(
                acquisition_dir, alignment, query=query
            )
        elif self == ModeEnum.MetaXpressSinglePlaneAcquisition:
            return fractal_faim_ipa.imagexpress_zmb.SinglePlaneAcquisition(
                acquisition_dir, alignment, query=query
            )
        elif self == ModeEnum.MetaXpressMixedAcquisition:
            return fractal_faim_ipa.imagexpress_zmb.MixedAcquisition(
                acquisition_dir, alignment, query=query
            )
        elif self == ModeEnum.MetaXpressSinglePlaneAcquisition_as3D:
            return fractal_faim_ipa.imagexpress_zmb.SinglePlaneAcquisition_as3D(
                acquisition_dir, alignment, query=query
            )
        else:
            raise NotImplementedError(f"MD Converter was not implemented for {self=}")
