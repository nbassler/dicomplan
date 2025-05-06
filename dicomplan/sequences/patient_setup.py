# import pydicom
from pydicom.dataset import Dataset


def patient_setup() -> Dataset:
    """
    Create a PatientSetup item (300A,0180).
    """
    ps = Dataset()
    ps.PatientSetupNumber = 1           # 300A,0182
    ps.PatientPosition = 'HFS'          # 0018,5100
    ps.SetupTechnique = 'ISOCENTRIC'    # 300A,01B0
    return ps
