# import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence


def fraction_group(dose_reference_uid: str) -> Dataset:
    """
    Create a FractionGroup item (300A,0070) with a single referenced beam.
    """
    fg = Dataset()
    fg.FractionGroupNumber = 1                          # 300A,0071
    fg.NumberOfFractionsPlanned = 1                     # 300A,0078
    fg.NumberOfBeams = 1                                # 300A,0080
    fg.NumberOfBrachyApplicationSetups = 0              # 300A,00A0
    fg.ReferencedBeamSequence = Sequence([_referenced_beam(dose_reference_uid)])  # 300C,0004
    return fg


def _referenced_beam(dose_reference_uid: str) -> Dataset:
    """
    Create a ReferencedBeam item (part of 300C,0004).
    """
    rb = Dataset()
    rb.BeamDose = 1.0                                   # 300A,0084
    rb.BeamMeterSet = 1.0                               # 300A,0086
    rb[0x3249, 0x0010] = 'Varian Medical Systems VISION 3249'  # Private creator
    rb[0x3249, 0x1000] = dose_reference_uid.encode('ascii')    # Private tag
    return rb
