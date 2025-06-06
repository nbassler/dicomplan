import pydicom
import struct
# from pydicom import Dataset
# from pydicom.sequence import Sequence
from dicomplan.sequences.ion_control_point import ion_control_points


def ion_beam() -> pydicom.Dataset:
    """
    Create an IonControlPointSequence with a single item.
    """
    ib = pydicom.Dataset()

    ib.Manufacturer = 'Varian Medical System Particle Therapy'  # 0008,0070
    ib.ManufacturerModelName = 'VPT'  # 0008,01090
    ib.TreatmentMachineName = 'TR4'  # 300a,00b2
    ib.PrimaryDosimeterUnit = 'MU'  # 300a,00b3
    ib.BeamNumber = 1  # 300a,00c0
    ib.BeamName = 'Field 1'  # 300a,00c2
    ib.BeamType = 'STATIC'  # 300a,00c4
    ib.RadiationType = 'PROTON'  # 300a,00c6
    ib.TreatmentDeliveryType = 'TREATMENT'  # 300a,00ce
    ib.NumberOfWedges = 0  # 300a,00d0
    ib.NumberOfCompensators = 0  # 300a,00e0
    ib.NumberOfBoli = 0  # 300a,00ed
    ib.NumberOfBlocks = 0  # 300a,00f0

    ib.FinalCumulativeMetersetWeight = 16.0  # 300a,010e
    ib.NumberOfControlPoints = 2  # 300a,0110  #TODO
    ib.ScanMode = 'MODULATED'  # 300a,0308
    ib.VirtualSourceAxisDistances = [2000.0, 2560.0]  # 300a,030a
    ib.SnoutSequence = pydicom.Sequence([snout()])
    ib.NumberOfRangeShifters = 0  # 300a,0312
    ib.NumberOfLateralSpreadingDevices = 2  # 300a,0330
    ib.LateralSpreadingDeviceSequence = pydicom.Sequence(lateral_spreading_device())  # 300a,0332
    ib.NumberOfRangeModulators = 0  # 300a,0340
    ib.PatientSupportType = 'TABLE'  # 300a,0350
    ib.PatientSupportID = 'Couch'  # 300a,0352
    ib.PatientSupportAccessoryCode = 'AC123'  # 300a,0354
    ib.IonControlPointSequence = pydicom.Sequence(ion_control_points())  # 300a,03a8

    ib[0x300b, 0x0010] = pydicom.DataElement(0x300b0010, 'SH', 'IMPAC')                    # 300b,0010 (unknown)
    ib[0x300b, 0x1002] = pydicom.DataElement(0x300b1002, 'UN', struct.pack('<f', 500.0))
    ib[0x300b, 0x1004] = pydicom.DataElement(0x300b1004, 'UN', struct.pack('<f', 85.00868225097656))
    ib[0x300b, 0x100e] = pydicom.DataElement(0x300b100e, 'UN', struct.pack('<f', 31.185909271240234))

    # ib[0x300b, 0x1002] = pydicom.DataElement(0x300b1002, 'DS', struct.pack('<f', 500.0))   # 300b,1002 (unknown)
    # ib[0x300b, 0x1004] = pydicom.DataElement(0x300b1004, 'DS', 85.00868225097656)          # 300b,1004 (unknown)
    # ib[0x300b, 0x100e] = pydicom.DataElement(0x300b100e, 'DS', 31.185909271240234)         # 300b,100e (unknown)

    ib.ReferencedPatientSetupNumber = 1     # 300c,006a
    ib.ReferencedToleranceTableNumber = 1   # 300c,00a0

    return ib


def snout() -> pydicom.Dataset:
    """
    Create a SnoutSequence with a single item.
    """
    sn = pydicom.Dataset()
    sn.SnoutID = 'S1'  # 300a,030f
    return sn


def lateral_spreading_device() -> list[pydicom.Dataset]:
    """
    Create a LateralSpreadingDeviceSequence with two items (X and Y).
    """
    lsd_x = pydicom.Dataset()
    lsd_x.LateralSpreadingDeviceNumber = 1  # 300a,0334
    lsd_x.LateralSpreadingDeviceID = 'MagnetX'  # 300a,0336
    lsd_x.LateralSpreadingDeviceType = 'MAGNET'  # 300a,0338

    lsd_y = pydicom.Dataset()
    lsd_y.LateralSpreadingDeviceNumber = 2  # 300a,0334
    lsd_y.LateralSpreadingDeviceID = 'MagnetY'  # 300a,0336
    lsd_y.LateralSpreadingDeviceType = 'MAGNET'  # 300a,0338

    return [lsd_x, lsd_y]
