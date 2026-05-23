import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function ImageToSvgPage() {
  return (
    <FileConverterForm
      title="Image to SVG"
      description="Upload a PNG or JPEG image and trace it into an SVG file."
      endpoint="/api/image-to-svg"
      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
      helperText="PNG, JPG, and JPEG files up to 10MB"
      downloadFilename="converted.svg"
      downloadLabel="Download SVG"
      successMessage="SVG is ready."
    />
  );
}

