from pydicom import DataElement
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
    rb.BeamMeterset = 1.0                               # 300A,0086
    rb[0x3249, 0x0010] = DataElement(0x32490010, 'LO', 'Varian Medical Systems VISION 3249')
    rb[0x3249, 0x1000] = DataElement(0x32491000, 'UI', dose_reference_uid.encode('ascii'))    # Private tag
    return rb
