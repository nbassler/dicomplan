import pydicom


def ion_control_point() -> pydicom.Dataset:
    """
    Create an IonControlPointSequence with a single item.
    """
    icp = pydicom.Dataset()

    icp.ControlPointIndex = 0                                     # 300a,0112
    icp.NominalBeamEnergy = 100.0                                 # 300a,0114
    icp.GantryAngle = 0.0                                         # 300a,011e
    icp.GantryRotationDirection = 'NONE'                          # 300a,011f
    icp.BeamLimitingDeviceAngle = 0.0                             # 300a,0120
    icp.BeamLimitingDeviceRotationDirection = 'NONE'              # 300a,0121
    icp.PatientSupportAngle = 0.0                                 # 300a,0122
    icp.PatientSupportRotationDirection = 'NONE'                  # 300a,0123
    icp.TableTopVerticalPosition = 0.0                            # 300a,0128
    icp.TableTopLongitudinalPosition = 0.0                        # 300a,0129
    icp.TableTopLateralPosition = 0.0                             # 300a,012a
    icp.IsocenterPosition = [0.0, 0.0, 0.0]                       # 300a,012c

    icp.CumulativeMetersetWeight = 0.0                            # 300a,0134

    icp.TableTopPitchAngle = 0.0                                  # 300a,0140
    icp.TableTopPitchRotationDirection = 'NONE'                   # 300a,0142
    icp.TableTopRollAngle = 0.0                                   # 300a,0144
    icp.TableTopRollRotationDirection = 'NONE'                    # 300a,0146
    icp.GantryPitchAngle = 0.0                                    # 300a,014a
    icp.GantryPitchRotationDirection = 'NONE'                     # 300a,014c
    icp.SnoutPosition = 421.0                                     # 300a,030d
    icp.MetersetRate = 0.0                                        # 300a,035a

    icp.LateralSpreadingDeviceSequence = pydicom.Sequence([lateral_spreading_device()])  # 300a,0370

    icp.ScanSpotTuneID = '4.0'                                    # 300a,0390

    icp.NumberOfScanSpotPositions = 1                             # 300a,0392
    icp.ScanSpotPositionMap = [0.0, 0.0]                          # 300a,0394
    icp.ScanSpotMetersetWeights = [16.0]                          # 300a,0396
    icp.ScanningSpotSize = [11.3, 11.2]                            # 300a,0398
    icp.NumberOfPaintings = 1                                     # 300a,039a

    # Private Tag (IMPAC)
    icp[0x300b, 0x0010] = 'IMPAC'                                 # 300b,0010
    icp[0x300b, 0x1017] = b'x\xaf\xaaB'                           # 300b,1017  unknown,
    # but similar to  (300B,1004) 85.00868225097656 4-byte float little endian
    # struct.unpack('<f', b'x\xaf\xaaB')  # → (85.33678436279297,)

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


def referenced_dose_reference(coefficient: float = 1.0) -> pydicom.Dataset:
    rdr = pydicom.Dataset()
    rdr.CumulativeDoseReferenceCoefficient = coefficient  # 300a,010c
    rdr.ReferencedDoseReferenceNumber = 1                 # 300c,0051
    return rdr
