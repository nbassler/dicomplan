import pydicom


def ion_tolerance_table():
    """
    Create an IonToleranceTable item.
    """
    it = pydicom.Dataset()
    it.ToleranceTableNumber = 1         # 300a,0042
    it.ToleranceTableLabel = 'T1'       # 300a,0043
    it.GantryAngleTolerance = 0.5       # 300a,0044
    it.BeamLimitingDeviceToleranceSequence = pydicom.Sequence()                         # 300a,0048
    it.BeamLimitingDeviceToleranceSequence.append(pydicom.Dataset())
    it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDevicePositionTolerance = 0   # 300a,004a
    it.BeamLimitingDeviceToleranceSequence[0].RTBeamLimitingDeviceType = 'X'              # 300a,00b8
    it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDevicePositionTolerance = 0   # 300a,004a
    it.BeamLimitingDeviceToleranceSequence[0].RTBeamLimitingDeviceType = 'Y'              # 300a,00b8
    it.SnoutPositionTolerance = 5.0                                                     # 300a,004b
    it.PatientSupportAngleTolerance = 3                                                 # 300a,004c

    it.TableTopPitchAngleTolerance = 3.0                # 300a,004f
    it.TableTopRollAngleTolerance = 3.0                 # 300a,0050

    it.TableTopVerticalPositionTolerance = 20.0         # 300a,0051
    it.TableTopLongitudinalPositionTolerance = 20.0     # 300a,0052
    it.TableTopLateralPositionTolerance = 20.0          # 300a,0053
    return it
