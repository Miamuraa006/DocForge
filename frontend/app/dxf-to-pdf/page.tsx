import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function DxfToPdfPage() {
  return (
    <FileConverterForm
      title="DXF to PDF"
      description="Upload a DXF drawing and convert it to PDF."
      endpoint="/api/dxf-to-pdf"
      accept=".dxf"
      helperText="DXF files up to 10MB"
    />
  );
}

