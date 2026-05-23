import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function SvgToDxfPage() {
  return (
    <FileConverterForm
      title="SVG to DXF"
      description="Upload an SVG vector file and convert it to DXF."
      endpoint="/api/svg-to-dxf"
      accept=".svg,image/svg+xml"
      helperText="SVG files up to 10MB"
      downloadFilename="converted.dxf"
      downloadLabel="Download DXF"
      successMessage="DXF is ready."
    />
  );
}

