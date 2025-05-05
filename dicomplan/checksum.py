import sys
import hashlib
import pydicom
import xml.etree.ElementTree as ET
from io import BytesIO
from pydicom.filebase import DicomBytesIO
from pydicom.filewriter import write_dataset
from pydicom.tag import Tag

# --- Step 1: Extract and parse the XML blob ---


def parse_referenced_indices(ds):
    xml_tag = Tag(0x3253, 0x1000)
    if xml_tag not in ds:
        print("XML blob (3253,1000) not found.")
        return None

    xml_blob = ds[xml_tag].value
    try:
        root = ET.fromstring(xml_blob.decode('windows-1252'))
    except Exception as e:
        print(f"Failed to parse XML: {e}")
        return None

    refs = {
        "Beam": [],
        "Tolerance": [],
        "DoseRef": []
    }

    for beam in root.findall(".//Beam"):
        num = beam.findtext("ReferencedBeamNumber")
        if num:
            refs["Beam"].append(int(num))

    for tol in root.findall(".//ToleranceTable"):
        num = tol.findtext("ReferencedToleranceTableNumber")
        if num:
            refs["Tolerance"].append(int(num))

    for dr in root.findall(".//DoseReference"):
        num = dr.findtext("ReferencedDoseReferenceNumber")
        if num:
            refs["DoseRef"].append(int(num))

    return refs

# --- Step 2: Extract matching elements ---


def extract_referenced_structures(ds, refs):
    new_ds = pydicom.Dataset()
    new_ds.file_meta = ds.file_meta

    if "BeamSequence" in ds:
        new_seq = []
        for item in ds.BeamSequence:
            if item.BeamNumber in refs["Beam"]:
                new_seq.append(item)
        new_ds.BeamSequence = new_seq

    if "ToleranceTableSequence" in ds:
        new_seq = []
        for item in ds.ToleranceTableSequence:
            if item.ToleranceTableNumber in refs["Tolerance"]:
                new_seq.append(item)
        new_ds.ToleranceTableSequence = new_seq

    if "DoseReferenceSequence" in ds:
        new_seq = []
        for item in ds.DoseReferenceSequence:
            if item.DoseReferenceNumber in refs["DoseRef"]:
                new_seq.append(item)
        new_ds.DoseReferenceSequence = new_seq

    return new_ds

# --- Step 3: Serialize and hash ---


def calculate_md5(dataset):
    fp = DicomBytesIO()
    fp.is_implicit_VR = (dataset.file_meta.TransferSyntaxUID == pydicom.uid.ImplicitVRLittleEndian)
    fp.is_little_endian = True
    write_dataset(fp, dataset)
    return hashlib.md5(fp.getvalue()).hexdigest().upper()

# --- Step 4: Run all ---


def main():
    if len(sys.argv) != 2:
        print("Usage: python checksum_from_xml_references.py <dicom_file>")
        sys.exit(1)

    path = sys.argv[1]
    ds = pydicom.dcmread(path)

    embedded_hash1 = 'EBF9DECBAE52D46C1845D37FE34DC63C'
    embedded_hash2 = 'DC82F9C5879609AE92C43949F3BD8308'

    refs = parse_referenced_indices(ds)
    if refs is None:
        return

    print("Referenced Beam Numbers:", refs["Beam"])
    print("Referenced Tolerance Tables:", refs["Tolerance"])
    print("Referenced Dose References:", refs["DoseRef"])

    subset_ds = extract_referenced_structures(ds, refs)
    md5 = calculate_md5(subset_ds)
    print(f"\nMD5 from referenced structures: {md5}")

    if md5 == embedded_hash1:
        print("Matches Embedded Hash 1!")
    elif md5 == embedded_hash2:
        print("Matches Embedded Hash 2!")
    else:
        print("No match.")


if __name__ == "__main__":
    main()
