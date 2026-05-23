import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function ImageToDxfPage() {
  return (
    <FileConverterForm
      title="Image to DXF"
      description="Upload a PNG or JPEG image and trace it into a DXF file."
      endpoint="/api/image-to-dxf"
      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
      helperText="PNG, JPG, and JPEG files up to 10MB"
      downloadFilename="converted.dxf"
      downloadLabel="Download DXF"
      successMessage="DXF is ready."
    />
  );
}

