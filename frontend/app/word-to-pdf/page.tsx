import { FileConverterForm } from "@/app/components/FileConverterForm";

export default function WordToPdfPage() {
  return (
    <FileConverterForm
      title="Word to PDF"
      description="Upload a Word document and convert it to PDF."
      endpoint="/api/word-to-pdf"
      accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      helperText=".doc and .docx files up to 10MB"
    />
  );
}

