import pydicom


def ion_control_points() -> pydicom.Dataset:
    """
    Create an IonControlPointSequence with at least two items.
    """
    icps = pydicom.Sequence()

    # first dataset is more verbose, than the rest.
    icp = pydicom.Dataset()
    icp.ControlPointIndex = 0                                     # 300a,0112
    icp.NominalBeamEnergy = 100.0                                 # 300a,0114
    icp.GantryAngle = 90.0                                         # 300a,011e
    icp.GantryRotationDirection = 'NONE'                          # 300a,011f
    icp.BeamLimitingDeviceAngle = 0.0                             # 300a,0120
    icp.BeamLimitingDeviceRotationDirection = 'NONE'              # 300a,0121
    icp.PatientSupportAngle = 0.0                                 # 300a,0122
    icp.PatientSupportRotationDirection = 'NONE'                  # 300a,0123
    icp.TableTopVerticalPosition = 0.0                            # 300a,0128
    icp.TableTopLongitudinalPosition = 0.0                        # 300a,0129
    icp.TableTopLateralPosition = 0.0                             # 300a,012a
    icp.IsocenterPosition = [0.0, 0.0, 0.0]                       # 300a,012c

    icp.CumulativeMetersetWeight = 0                             # 300a,0134

    icp.TableTopPitchAngle = 0.0                                  # 300a,0140
    icp.TableTopPitchRotationDirection = 'NONE'                   # 300a,0142
    icp.TableTopRollAngle = 0.0                                   # 300a,0144
    icp.TableTopRollRotationDirection = 'NONE'                    # 300a,0146
    icp.GantryPitchAngle = None                                    # 300a,014a
    icp.GantryPitchRotationDirection = None                     # 300a,014c
    icp.SnoutPosition = 421.0                                     # 300a,030d
    icp.MetersetRate = 100.0                                        # 300a,035a

    icp.LateralSpreadingDeviceSequence = pydicom.Sequence(lateral_spreading_device())  # 300a,0370

    icp.ScanSpotTuneID = '4.0'                                    # 300a,0390

    icp.NumberOfScanSpotPositions = 1                             # 300a,0392
    icp.ScanSpotPositionMap = [0.0, 0.0]                          # 300a,0394
    icp.ScanSpotMetersetWeights = [16.0]                       # 300a,0396
    icp.ScanningSpotSize = [11.3, 11.2]                            # 300a,0398
    icp.NumberOfPaintings = 1                                     # 300a,039a

    # Private Tag (IMPAC)
    icp[0x300b, 0x0010] = pydicom.DataElement(0x300b0010, 'SH', 'IMPAC')   # 300b,0010
    icp[0x300b, 0x1017] = pydicom.DataElement(0x300b1017, 'UN', b'x\xaf\xaaB')                           # 300b,1017  unknown,
    # but similar to  (300B,1004) 85.00868225097656 4-byte float little endian
    # struct.unpack('<f', b'x\xaf\xaaB')  # → (85.33678436279297,)

    icp.LateralSpreadingDeviceSequence = pydicom.Sequence(lateral_spreading_device())  # 300a,0370
    icp.ReferencedDoseReferenceSequence = pydicom.Sequence(referenced_dose_reference())  # 300c,0050

    icps.append(icp)

    # check if icpScanSpotMetersetWeights is iterable, and if it is, find the sum:
    if hasattr(icp.ScanSpotMetersetWeights, '__iter__'):
        cm = sum(icp.ScanSpotMetersetWeights)
    else:
        cm = icp.ScanSpotMetersetWeights

    new_cummulative_meterset_weight = icp.CumulativeMetersetWeight + cm
    icps.append(_ion_control_point_next(1, empty=True, cm=new_cummulative_meterset_weight))

    return icps


def _ion_control_point_next(idx: int, empty=False, cm=0.0) -> pydicom.Dataset:
    """
    Create an IonControlPointSequence with a single item.
    """
    icp = pydicom.Dataset()
    icp.ControlPointIndex = idx                                   # 300a,0112
    icp.NominalBeamEnergy = 100.0                                 # 300a,0114
    icp.CumulativeMetersetWeight = cm                             # 300a,0134
    icp.ScanSpotTuneID = '4.0'                                    # 300a,0390
    icp.NumberOfScanSpotPositions = 1                             # 300a,0392
    icp.ScanSpotPositionMap = [0.0, 0.0]                          # 300a,0394
    if empty:
        icp.ScanSpotMetersetWeights = [0.0]                       # 300a,0396
    else:
        icp.ScanSpotMetersetWeights = [16.0]                       # 300a,0396
    icp.NumberOfPaintings = 1                                     # 300a,039a
    icp[0x300b, 0x0010] = pydicom.DataElement(0x300b0010, 'SH', 'IMPAC')   # 300b,0010
    icp[0x300b, 0x1017] = pydicom.DataElement(0x300b1017, 'UN', b'Qs\xa1B')    # 300b,1017  unknown,

    # TODO calculate dose coefficient
    dose_coefficient = 1.0
    icp.ReferencedDoseReferenceSequence = pydicom.Sequence(referenced_dose_reference(dose_coefficient))  # 300c,0050
    return icp


def lateral_spreading_device() -> list[pydicom.Dataset]:
    """
    Create a LateralSpreadingDeviceSequence with a single item.
    """

    lsd1 = pydicom.Dataset()
    lsd1.LateralSpreadingDeviceWaterEquivalentThickness = 0.0    # 300a,033c
    lsd1.LateralSpreadingDeviceSetting = 'IN'                    # 300a,0372
    lsd1.IsocenterToLateralSpreadingDeviceDistance = 2000.0      # 300a,0374
    lsd1.ReferencedLateralSpreadingDeviceNumber = 1              # 300c,0102

    lsd2 = pydicom.Dataset()
    lsd2.LateralSpreadingDeviceWaterEquivalentThickness = 0.0
    lsd2.LateralSpreadingDeviceSetting = 'IN'
    lsd2.IsocenterToLateralSpreadingDeviceDistance = 2560.0
    lsd2.ReferencedLateralSpreadingDeviceNumber = 2

    return [lsd1, lsd2]


def referenced_dose_reference(coefficient: float = 0) -> list[pydicom.Dataset]:
    rdr = pydicom.Dataset()
    rdr.CumulativeDoseReferenceCoefficient = coefficient  # 300a,010c
    rdr.ReferencedDoseReferenceNumber = 1                 # 300c,0051
    return [rdr]
