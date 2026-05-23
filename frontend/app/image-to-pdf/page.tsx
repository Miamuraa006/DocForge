import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function ImageToPdfPage() {
  return (
    <FileConverterForm
      title="Image to PDF"
      description="Upload an image and convert it to PDF."
      endpoint="/api/image-to-pdf"
      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
      helperText="JPG, JPEG, and PNG files up to 10MB"
    />
  );
}

