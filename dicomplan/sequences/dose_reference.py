import pydicom


def dose_reference():
    """
    Create a single item for the DoseReferenceSequence.
    """
    ds = pydicom.Dataset()
    ds.DoseReferenceNumber = 1                          # (300a,0012)
    # ds.DoseReferenceUID = pydicom.uid.generate_uid()    # (300a,0013)
    ds.DoseReferenceUID = '1.2.246.352.71.10.361940808526.5131.20190916150554'
    ds.DoseReferenceStructureType = 'SITE'              # (300a,0014)
    ds.DoseReferenceDescription = 'Target'              # (300a,0016)
    ds.DoseReferenceType = 'ORGAN_AT_RISK'              # (300a,0020)
    # ds.DoseReferencePointCoordinates = [0.0, 0.0, 0.0]   # (300a,0022)
    ds.DeliveryMaximumDose = '2'                        # (300a,0023)
    ds.OrganAtRiskMaximumDose = '2'                     # (300a,002c)

    # Optional Varian private tag
    ds[0x3267, 0x0010] = pydicom.DataElement(0x32670010, 'LO', 'Varian Medical Systems VISION 3267')
    ds[0x3267, 0x1000] = pydicom.DataElement(0x32671000, 'UN', b'Target')

    return ds
