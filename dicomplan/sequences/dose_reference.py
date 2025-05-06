import pydicom


def dose_reference():
    """
    Create a single item for the DoseReferenceSequence.
    """
    ds = pydicom.Dataset()
    ds.DoseReferenceNumber = 1                          # (300a,0012)
    ds.DoseReferenceUID = pydicom.uid.generate_uid()    # (300a,0013)
    ds.DoseReferenceStructureType = 'SITE'              # (300a,0014)
    ds.DoseReferenceDescription = 'Target'              # (300a,0016)
    ds.DoseReferenceType = 'POINT'                      # (300a,0020)
    ds.DoseReferencePointCoordinates = [0.0, 0.0, 0.0]   # (300a,0022)
    ds.DeliveryMaximumDose = 1.0                        # (300a,0023)
    ds.PointDose = 1.0                                  # (300a,0024)

    # Optional Varian private tag
    ds[0x3267, 0x0010] = 'Varian Medical Systems VISION 3267'
    ds[0x3267, 0x1000] = b'Target'

    return ds
