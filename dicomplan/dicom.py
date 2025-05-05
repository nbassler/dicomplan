import pydicom
import logging
import xml.etree.ElementTree as ET
import numpy as np

logger = logging.getLogger(__name__)


class Dicom:
    def __init__(self):
        self.ds = pydicom.Dataset()
        self._set_static_tags()

    @classmethod
    def create_new_dataset(cls, args):
        dataset = pydicom.Dataset()

        dataset.PatientName = args.patient_name
        dataset.PatientID = args.patient_id
        dataset.ReviewerName = args.reviewer_name
        dataset.OperatorName = args.operator_name

        return dataset

    def _set_static_tags(self):
        """
        Set static DICOM tags for the dataset.
        """
        self.ds.SpecificCharacterSet = 'ISO_IR 192'         # 0008,0005
        self.ds.InstanceCreationDate = '20250101'           # 0008,0012
        self.ds.InstanceCreationTime = '120000'             # 0008,0013
        self.ds.SOPClassUID = pydicom.uid.generate_uid()    # 0008,0016
        self.ds.SOPInstanceUID = pydicom.uid.generate_uid()  # 0008,0018
        self.ds.StudyDate = '20250101'                      # 0008,0020
        self.ds.StudyTime = '120000'                        # 0008,0030
        self.ds.AccessionNumber = ''                        # 0008,0050
        self.ds.Modality = 'RTPLAN'                         # 0008,0060
        self.ds.Manufacturer = 'Varian Medical Systems'     # 0008,0070
        self.ds.ReferringPhysicianName = ''                 # 0008,0090
        self.ds.StationName = 'VADB101'                     # 0008,1010
        self.ds.StudyDescription = ''                       # 0008,1030
        self.ds.SeriesDescription = 'ARIA RadOnc Plans'     # 0008,103e
        self.ds.OperatorName = 'DefaultOperator'            # 0008,1070
        self.ds.ManufacturersModelName = 'ARIA RadOnc'      # 0008,1090

        self.ds.PatientName = 'DefaultName'                 # 0010,0010
        self.ds.PatientID = 'DefaultID'                     # 0010,0020
        self.ds.PatientBirthDate = '19700101'               # 0010,0030
        self.ds.PatientSex = ''                             # 0010,0040

        self.ds.DeviceSerialNumber = '123456789012'         # 0018,1000
        self.ds.SoftwareVersions = '0.0'                    # 0018,1020

        self.ds.StudyInstanceUID = pydicom.uid.generate_uid()   # 0020,000d
        self.ds.SeriesInstanceUID = pydicom.uid.generate_uid()  # 0020,000e
        self.ds.StudyID = 'Phantom1'                            # 0020,0010
        self.ds.SeriesNumber = '1'                              # 0020,0011
        self.ds.FrameOfReferenceUID = pydicom.uid.generate_uid()   # 0020,0052
        self.ds.PositionReferenceIndicator = ''                 # 0020,1040

        self.ds.RTPlanLabel = 'DefaultLabel'                 # 300a,0002
        self.ds.RTPlanDate = '20250101'                      # 300a,0006
        self.ds.RTPlanTime = '120000'                        # 300a,0007
        self.ds.PlanIntent = 'CURATIVE'                      # 300a,000a
        self.ds.RTPlanGeometry = 'PATIENT'                   # 300a,000c
        self.ds.DoseReferenceSequence = self._dose_reference_sequence()  # 300a,0010
        self.ds.FractionGroupSequence = self._fraction_group_sequence(
            self.ds.DoseReferenceSequence[0].DoseReferenceUID)  # 300a,0070
        self.ds.PatientSetupSequence = self._patient_setup_sequence()  # 300a,0180
        self.ds.IonToleranceTableSequence = self._ion_tolerance_table_sequence()  # 300a,03a0
        self.ds.IonControlPointSequence = self._ion_control_point_sequence()  # 300a,03a2
        self.ds.ReferencedStructureSetSequence = self._referenced_structure_set_sequence()  # 300c,0060

        self.ds[0x300b, 0x0010] = 'IMPAC'           # 300b,0010
        self.ds[0x300b, 0x1008] = b'v1'             # 300b,1008

        self.ds.ApprovalStatus = 'APPROVED'         # 300e,0002
        self.ds.ReviewDate = '20250101'             # 300e,0004
        self.ds.ReviewTime = '120000'               # 300e,0005
        self.ds.ReviewerName = 'DefaultReviewer'    # 300e,0008

        # Generate the XML string and its length
        xml_string = self._generate_xml_string()
        xml_length = len(xml_string)

        # Set the private tag with the XML string
        self.ds[0x3253, 0x0010] = 'Varian Medical Systems VISION 3253'
        self.ds[0x3253, 0x1000] = pydicom.DataElement(0x32531000, 'LO', xml_string)
        self.ds[0x3253, 0x1001] = pydicom.DataElement(0x32531001, 'US', xml_length)

        logging.debug(f"XML string: {xml_string}")
        logging.debug(f"XML string length: {xml_length}")

        self.ds[0x3253, 0x1002] = ''

        self.ds[0x3287, 0x0010] = 'Varian Medical Systems VISION 3287'
        self.ds[0x3287, 0x1000] = self._generate_checksum()

    @staticmethod
    def _fraction_group_sequence(dose_reference_uid):
        """
        Create a FractionGroupSequence with a single item.
        """
        fgs = pydicom.Sequence()                            # 300a,0070
        fg = pydicom.Dataset()
        fg.FractionGroupNumber = 1                          # 300a,0071
        fg.NumberOfFractionsPlanned = 1                     # 300a,0078
        fg.NumberOfBeams = 1                                # 300a,0080
        fg.NumberOfBrachyApplicationSetups = 0              # 300a,00a0
        fg.ReferencedBeamSequence = pydicom.Sequence()      # 300c,0004
        fg.ReferencedBeamSequence.append(pydicom.Dataset())
        fg.ReferencedBeamSequence[0].BeamDose = 1.0         # 300a,0084
        fg.ReferencedBeamSequence[0].BeamMeterSet = 1.0     # 300a,0086
        fg.ReferencedBeamSequence[0][0x3249, 0x0010] = 'Varian Medical Systems VISION 3249'     # 3249,0010
        fg.ReferencedBeamSequence[0][0x3249, 0x1000] = dose_reference_uid.encode('ascii')       # 3249,1000
        fgs.append(fg)
        return fgs

    @staticmethod
    def _patient_setup_sequence():
        """
        Create a PatientSetupSequence with a single item.
        """
        pss = pydicom.Sequence()            # 300a,0180
        ps = pydicom.Dataset()
        ps.PatientPosition = 'HFS'          # 0018,5100
        ps.PatientSetupNumber = 1           # 300a,0182
        ps.SetupTechnique = 'ISOCENTRIC'    # 300a,01b0
        return pss

    @staticmethod
    def _ion_tolerance_table_sequence():
        """
        Create an IonToleranceTableSequence with a single item.
        """
        its = pydicom.Sequence()            # 300a,03a0
        it = pydicom.Dataset()
        it.IonToleranceTableNumber = 1      # 300a,0042
        it.ToleranceTableLabel = 'T1'       # 300a,0043
        it.GantryAngleTolerance = 0.5       # 300a,0044
        it.BeamLimitingDeviceToleranceSequence = pydicom.Sequence()                         # 300a,0048
        it.BeamLimitingDeviceToleranceSequence.append(pydicom.Dataset())
        it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDevicePositionTolerance = 0   # 300a,004a
        it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDeviceType = 'X'              # 300a,00b8
        it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDevicePositionTolerance = 0   # 300a,004a
        it.BeamLimitingDeviceToleranceSequence[0].BeamLimitingDeviceType = 'Y'              # 300a,00b8
        it.SnoutPositionTolerance = 5.0                                                     # 300a,004b
        it.PatientSupportAngleTolerance = 3                                                 # 300a,004c

        it.TableTopPitchAngleTolerance = 3.0                # 300a,004f
        it.TableTopRollAngleTolerance = 3.0                 # 300a,0050

        it.TableTopVerticalPositionTolerance = 20.0         # 300a,0051
        it.TableTopLongitudinalPositionTolerance = 20.0     # 300a,0052
        it.TableTopLateralPositionTolerance = 20.0          # 300a,0053
        return its

    @staticmethod
    def _ion_control_point_sequence():
        """
        Create an IonControlPointSequence with a single item.
        """
        ics = pydicom.Sequence()
        ic = pydicom.Dataset()

        # TODO
        ics.append(ic)
        return ics

    @staticmethod
    def _referenced_structure_set_sequence():
        """
        Create a ReferencedStructureSetSequence with a single item.
        """
        rss = pydicom.Sequence()
        rs = pydicom.Dataset()
        rs.ReferencedSOPClassUID = pydicom.uid.generate_uid()       # 0008,1150
        rs.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()    # 0008,1155
        rss.append(rs)
        return rss

    @staticmethod
    def _generate_xml_string():
        """
        Generate the XML string for the private tag using xml.etree.ElementTree.
        """
        root = ET.Element("ExtendedVAPlanInterface", Version="1")

        beams = ET.SubElement(root, "Beams")
        beam = ET.SubElement(beams, "Beam")
        ET.SubElement(beam, "ReferencedBeamNumber").text = "1"
        beam_extension = ET.SubElement(beam, "BeamExtension")
        ET.SubElement(beam_extension, "FieldOrder").text = "1"
        ET.SubElement(beam_extension, "GantryRtnExtendedStart").text = "false"
        ET.SubElement(beam_extension, "GantryRtnExtendedStop").text = "false"

        tolerance_tables = ET.SubElement(root, "ToleranceTables")
        tolerance_table = ET.SubElement(tolerance_tables, "ToleranceTable")
        ET.SubElement(tolerance_table, "ReferencedToleranceTableNumber").text = "1"
        tolerance_table_extension = ET.SubElement(tolerance_table, "ToleranceTableExtension")
        ET.SubElement(tolerance_table_extension, "CollXSetup").text = "Automatic"
        ET.SubElement(tolerance_table_extension, "CollYSetup").text = "Automatic"

        dose_references = ET.SubElement(root, "DoseReferences")
        dose_reference = ET.SubElement(dose_references, "DoseReference")
        ET.SubElement(dose_reference, "ReferencedDoseReferenceNumber").text = "1"
        dose_reference_extension = ET.SubElement(dose_reference, "DoseReferenceExtension")
        ET.SubElement(dose_reference_extension, "DailyDoseLimit").text = "2"
        ET.SubElement(dose_reference_extension, "SessionDoseLimit").text = "2"

        xml_string = ET.tostring(root, encoding='Windows-1252', xml_declaration=True)
        return xml_string

    @staticmethod
    def _dose_reference_sequence():
        drs = pydicom.Sequence()                            # 300a,0010
        dr = pydicom.Dataset()
        dr.DoseReferenceNumber = 1                          # 300a,0012
        dr.DoseReferenceUID = pydicom.uid.generate_uid()    # 300a,0013
        dr.DoseReferenceStructureType = 'SITE'              # 300a,0014
        dr.DoseReferenceDescription = 'Target'              # 300a,0016
        dr.DoseReferenceType = 'POINT'                      # 300a,0020
        dr.DoseReferencePointCoordinates = [0.0, 0.0, 0.0]  # 300a,0022
        dr.DeliveryMaximumDose = 1.0                        # 300a,0023
        dr.PointDose = 1.0                                  # 300a,0024

        dr[0x3267, 0x0010] = 'Varian Medical Systems VISION 3267'
        dr[0x3267, 0x1000] = b'Target'

        drs.append(dr)
        return drs

    @staticmethod
    def _generate_checksum():
        """
        Generate the mixed content byte string for the private tag.
        b'\xfe\xff\x00\xe0\\\x00\x00\x00\x872\x10\x00"\x00\x00\x00' +
        b'Varian Medical Systems VISION 3287\x872\x01\x10 \x00\x00\x00' +
        b'EBF9DECBAE52D46C1845D37FE34DC63C\x872\x02\x10\x02\x00\x00\x002 ' +
        b'\xfe\xff\x00\xe0\\\x00\x00\x00\x872\x10\x00"\x00\x00\x00' +
        b'Varian Medical Systems VISION 3287\x872\x01\x10 \x00\x00\x00' +
        b'DC82F9C5879609AE92C43949F3BD8308\x872\x02\x10\x02\x00\x00\x001 '
        """
        header = b'\xfe\xff\x00\xe0\\\x00\x00\x00\x872\x10\x00"\x00\x00\x00'
        text_block = b'Varian Medical Systems VISION 3287'
        checksum_identifier = b'\x872\x01\x10 \x00\x00\x00'

        # from https://groups.google.com/g/python-medphys/c/3_BQNBNBL-g
        # a) Plan Integrity Sequence (3287,xx00): This introduces a sequence of checksums
        # on dose-relevant data in the RT Plan. This sequence is imported and exported only
        # if the Approval Module is present and the Approval Status (300E,0002) has the value "APPROVED."
        # b) Plan Integrity Hash (3287,xx01): It's a hash value calculated from selected data in the RT Plan
        # using a specific algorithm.
        # c) Plan Integrity Hash Version (3287,xx02): This indicates the version of the hash algorithm used to
        # calculate the value of the Plan Integrity Hash.
        # So they these are probably md5sums, and probably here both b) and c) is stored in 3287,1000?
        #
        # I have no info on what tags were used to calculate the hash, maybe related to the
        # 0x3253, 0x1000 XML string?
        #
        hex_string_1 = b'EBF9DECBAE52D46C1845D37FE34DC63C'
        hex_string_2 = b'DC82F9C5879609AE92C43949F3BD8308'
        separator_1 = b'2 '
        separator_2 = b'1 '

        # Construct the mixed content byte string
        mixed_content = (
            header +
            text_block +
            checksum_identifier +
            hex_string_1 +
            checksum_identifier +
            hex_string_1 +
            separator_1 +

            header +
            text_block +
            checksum_identifier +
            hex_string_2 +
            checksum_identifier +
            separator_2
        )

        return mixed_content
