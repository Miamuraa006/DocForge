import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function VectorToPdfPage() {
  return (
    <FileConverterForm
      title="Vector to PDF"
      description="Upload an SVG vector file and convert it to PDF."
      endpoint="/api/vector-to-pdf"
      accept=".svg,image/svg+xml"
      helperText="SVG files up to 10MB"
    />
  );
}

