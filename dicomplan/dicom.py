import pydicom
from pydicom.uid import ImplicitVRLittleEndian

import datetime
import logging
import xml.etree.ElementTree as ET
import numpy as np

from sequences.dose_reference import dose_reference
from sequences.fraction_group import fraction_group
from sequences.patient_setup import patient_setup
from sequences.ion_tolerance_table import ion_tolerance_table
from sequences.ion_beam import ion_beam
from dicomplan.spots import generate_spot_pattern


logger = logging.getLogger(__name__)


class Dicom:
    def __init__(self):
        self.ds = pydicom.Dataset()
        self._set_static_tags()

    def apply_model(self, model):
        """
        Apply the model to the DICOM dataset.
        """

        logger.debug("apply_model()")

        self.ds.PatientName = model.plan_patient_name
        self.ds.PatientID = model.plan_patient_id
        self.ds.OperatorsName = model.plan_operator_name
        self.ds.ReviewerName = model.plan_reviewer_name
        self.ds.RTPlanLabel = model.plan_label

        # set current date and time
        now = datetime.datetime.now()
        self.ds.StudyDate = now.strftime('%Y%m%d')
        self.ds.StudyTime = now.strftime('%H%M%S.%f')[:-3]

        # get the spot pattern
        coords, weights = generate_spot_pattern(model)
        nspots = len(coords) // 2  # total number of spots
        zero_weights = np.zeros(nspots)
        logger.info(f"number of spots: {nspots}")

        # check if coords length is exactly 2*nspots
        if len(coords) != 2 * nspots:
            raise ValueError(f"coords length {len(coords)} is not equal to 2*nspots {2 * nspots}")

        # set total plan MU. For now there is only a single energy layer.
        total_mus = nspots * model.spot_mu
        self.ds.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamMeterset = total_mus
        logger.info(f"total MU: {total_mus}")

        cum_weight = 0.0

        # temporary for tests
        weights *= 40.0

        coords_mm = coords * 10.0  # convert to mm

        for _i, ib in enumerate(self.ds.IonBeamSequence):
            logger.debug(f"apply_model() - ion beam number {_i}")
            # set treatment machine
            ib.TreatmentMachineName = model.field_treatment_machine

            for cp_idx, icp in enumerate(ib.IonControlPointSequence):
                icp.ControlPointIndex = cp_idx
                icp.NominalBeamEnergy = model.spot_energy
                if cp_idx == 0:
                    icp.GantryAngle = model.field_gantry_angle
                    # TODO:set table positions
                    # TODO:set snout position
                icp.CumulativeMetersetWeight = cum_weight  # value before spots are delivered

                icp.NumberOfScanSpotPositions = nspots  # TODO: multiple layer handling.
                icp.ScanSpotPositionMap = coords_mm.tolist()

                # if control point index is even, fill weights, otherwise set to 0
                if icp.ControlPointIndex % 2 == 0:
                    icp.ScanSpotMetersetWeights = weights.tolist()
                    # we will let the cumulative weight range from 0 to 1.
                    cum_weight += sum(weights)
                else:
                    icp.ScanSpotMetersetWeights = zero_weights.tolist()
            ib.FinalCumulativeMetersetWeight = cum_weight
            logger.debug(f"apply_model() - FinalCumulativeMetersetWeight: {cum_weight}")

    def write(self, filename: str):
        """
        Write the DICOM dataset to a file.
        """
        # Set required file meta
        self.ds.file_meta = pydicom.Dataset()
        self.ds.file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
        self.ds.file_meta.MediaStorageSOPClassUID = self.ds.SOPClassUID
        self.ds.file_meta.MediaStorageSOPInstanceUID = self.ds.SOPInstanceUID
        self.ds.file_meta.ImplementationClassUID = pydicom.uid.PYDICOM_IMPLEMENTATION_UID

        # Save using the correct flags
        pydicom.dcmwrite(
            filename,
            self.ds,
            # write_like_original=False,
            enforce_file_format=True,
            implicit_vr=True,
            little_endian=True
        )

    def _set_static_tags(self):
        """
        Set static DICOM tags for the dataset.
        """
        self.ds.SpecificCharacterSet = 'ISO_IR 192'         # 0008,0005
        self.ds.InstanceCreationDate = '20250101'           # 0008,0012
        self.ds.InstanceCreationTime = '120000'             # 0008,0013
        # self.ds.SOPClassUID = pydicom.uid.generate_uid()    # 0008,0016
        # self.ds.SOPInstanceUID = pydicom.uid.generate_uid()  # 0008,0018

        self.ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.8'
        self.ds.SOPInstanceUID = '1.2.246.352.71.5.361940808526.21506.20191103151832'

        self.ds.StudyDate = '20250101'                      # 0008,0020
        self.ds.StudyTime = '124408.887'                    # 0008,0030
        self.ds.AccessionNumber = ''                        # 0008,0050
        self.ds.Modality = 'RTPLAN'                         # 0008,0060
        self.ds.Manufacturer = 'Varian Medical Systems'     # 0008,0070
        self.ds.ReferringPhysicianName = ''                 # 0008,0090
        self.ds.StationName = 'VADB101'                     # 0008,1010
        self.ds.StudyDescription = ''                       # 0008,1030
        self.ds.SeriesDescription = 'ARIA RadOnc Plans'     # 0008,103e
        self.ds.OperatorsName = 'DefaultOperator'            # 0008,1070
        self.ds.ManufacturerModelName = 'ARIA RadOnc'      # 0008,1090

        self.ds.PatientName = 'DefaultName'                 # 0010,0010
        self.ds.PatientID = 'DefaultID'                     # 0010,0020
        self.ds.PatientBirthDate = '19700101'               # 0010,0030
        self.ds.PatientSex = ''                             # 0010,0040

        self.ds.DeviceSerialNumber = '361940808526'         # 0018,1000
        self.ds.SoftwareVersions = '13.7.33'                    # 0018,1020

        # self.ds.StudyInstanceUID = pydicom.uid.generate_uid()   # 0020,000d
        # self.ds.SeriesInstanceUID = pydicom.uid.generate_uid()  # 0020,000e
        self.ds.StudyInstanceUID = '1.2.246.352.205.5379576546120926927.16596583169698917258'
        self.ds.SeriesInstanceUID = '1.2.246.352.71.2.361940808526.221621.20190916145704'

        self.ds.StudyID = 'Phantom1'                            # 0020,0010
        self.ds.SeriesNumber = '2'                              # 0020,0011
        # self.ds.FrameOfReferenceUID = pydicom.uid.generate_uid()   # 0020,0052
        self.ds.FrameOfReferenceUID = '1.2.246.352.205.5293866479401426372.4409618553988963736'
        self.ds.PositionReferenceIndicator = ''                 # 0020,1040

        self.ds.RTPlanLabel = 'DefaultLabel'                 # 300a,0002
        self.ds.RTPlanDate = '20250101'                      # 300a,0006
        self.ds.RTPlanTime = '162136.13'                        # 300a,0007
        self.ds.PlanIntent = 'CURATIVE'                      # 300a,000a
        self.ds.RTPlanGeometry = 'PATIENT'                   # 300a,000c

        # Build DoseReferenceSequence first so we can pass its UID to dependent structures
        dose_ref = dose_reference()
        self.ds.DoseReferenceSequence = pydicom.Sequence([dose_ref])  # 300a,0010

        # Other sequences
        fg = fraction_group(dose_ref.DoseReferenceUID)
        self.ds.FractionGroupSequence = pydicom.Sequence([fg])  # 300a,0070

        self.ds.PatientSetupSequence = pydicom.Sequence([patient_setup()])  # 300a,0180
        self.ds.IonToleranceTableSequence = pydicom.Sequence([ion_tolerance_table()])  # 300a,03a0
        self.ds.IonBeamSequence = pydicom.Sequence([ion_beam()])  # 300a,03a2
        self.ds.ReferencedStructureSetSequence = pydicom.Sequence([self._referenced_structure_set()])  # 300c,0060

        self.ds[0x300b, 0x0010] = pydicom.DataElement(0x300b0010, 'SH', 'IMPAC')  # 300b,0010
        self.ds[0x300b, 0x1008] = pydicom.DataElement(0x300b1008, 'UN', b'v1')    # 300b,1008

        self.ds.ApprovalStatus = 'APPROVED'         # 300e,0002
        self.ds.ReviewDate = '20250101'             # 300e,0004
        self.ds.ReviewTime = '162136.223'               # 300e,0005
        self.ds.ReviewerName = 'DefaultReviewer'    # 300e,0008

        # Generate the XML string and its length
        xml_string = self._generate_xml_string()
        xml_length = len(xml_string)
        length_bytes = str(xml_length).encode('ascii') + b' '

        # Set the private tag with the XML string
        self.ds[0x3253, 0x0010] = pydicom.DataElement(0x32530010, 'LO', 'Varian Medical Systems VISION 3253')
        self.ds[0x3253, 0x1000] = pydicom.DataElement(0x32531000, 'UN', xml_string)
        self.ds[0x3253, 0x1001] = pydicom.DataElement(0x32531001, 'UN', length_bytes)

        logging.debug(f"XML string: {xml_string}")
        logging.debug(f"XML string length: {xml_length}")

        self.ds[0x3253, 0x1002] = pydicom.DataElement(0x32531002, 'UN', b'ExtendedIF')

        self.ds[0x3287, 0x0010] = pydicom.DataElement(0x32870010, 'LO', 'Varian Medical Systems VISION 3287')
        # self.ds[0x3287, 0x1000] = pydicom.DataElement(0x32871000, 'UN', self._generate_checksum())

    @staticmethod
    def _referenced_structure_set():
        """
        Create a ReferencedStructureSetSequence with a single item.
        """
        rs = pydicom.Dataset()
        # rs.ReferencedSOPClassUID = pydicom.uid.generate_uid()       # 0008,1150
        rs.ReferencedSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
        # rs.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()    # 0008,1155
        rs.ReferencedSOPInstanceUID = '1.2.246.352.71.4.361940808526.12071.20190918133435'

        return rs

    @staticmethod
    def _generate_xml_string():
        """
        Generate the XML string for the private tag using xml.etree.ElementTree.
        """
        root = ET.Element("ExtendedVAPlanInterface", Version="1")

        _beams = ET.SubElement(root, "Beams")
        _beam = ET.SubElement(_beams, "Beam")
        ET.SubElement(_beam, "ReferencedBeamNumber").text = "1"
        _beam_ext = ET.SubElement(_beam, "BeamExtension")
        ET.SubElement(_beam_ext, "FieldOrder").text = "1"
        ET.SubElement(_beam_ext, "GantryRtnExtendedStart").text = "false"
        ET.SubElement(_beam_ext, "GantryRtnExtendedStop").text = "false"

        _tables = ET.SubElement(root, "ToleranceTables")
        _table = ET.SubElement(_tables, "ToleranceTable")
        ET.SubElement(_table, "ReferencedToleranceTableNumber").text = "1"
        _table_ext = ET.SubElement(_table, "ToleranceTableExtension")
        ET.SubElement(_table_ext, "CollXSetup").text = "Automatic"
        ET.SubElement(_table_ext, "CollYSetup").text = "Automatic"

        _refs = ET.SubElement(root, "DoseReferences")
        _ref = ET.SubElement(_refs, "DoseReference")
        ET.SubElement(_ref, "ReferencedDoseReferenceNumber").text = "1"
        _ref_ext = ET.SubElement(_ref, "DoseReferenceExtension")
        ET.SubElement(_ref_ext, "DailyDoseLimit").text = "2"
        ET.SubElement(_ref_ext, "SessionDoseLimit").text = "2"

        return ET.tostring(root, encoding='Windows-1252', xml_declaration=True)

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

        if len(mixed_content) % 2 == 1:
            mixed_content += b'\x00'

        return mixed_content
