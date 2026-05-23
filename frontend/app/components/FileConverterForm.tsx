"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2, Trash2, Upload, Wand2 } from "lucide-react";

type FileConverterFormProps = {
  title: string;
  description: string;
  endpoint: string;
  accept: string;
  helperText: string;
  downloadFilename?: string;
  downloadLabel?: string;
  successMessage?: string;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
const maxFileSize = 10 * 1024 * 1024;

function formatFileSize(size: number) {
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

export function FileConverterForm({
  title,
  description,
  endpoint,
  accept,
  helperText,
  downloadFilename = "converted.pdf",
  downloadLabel = "Download PDF",
  successMessage = "PDF is ready.",
}: FileConverterFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<"success" | "error" | null>(null);

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, [downloadUrl]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    setMessage(null);
    setMessageType(null);
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }

    if (selectedFile && selectedFile.size > maxFileSize) {
      setFile(null);
      event.target.value = "";
      setMessage("File size must be 10MB or less.");
      setMessageType("error");
      return;
    }

    setFile(selectedFile);
  }

  function clearFile() {
    setFile(null);
    setMessage(null);
    setMessageType(null);
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setMessage("Choose a file first.");
      setMessageType("error");
      return;
    }

    setIsConverting(true);
    setMessage(null);
    setMessageType(null);
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail ?? "Conversion failed.");
      }

      const blob = await response.blob();
      setDownloadUrl(URL.createObjectURL(blob));
      setMessage(successMessage);
      setMessageType("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Conversion failed.");
      setMessageType("error");
    } finally {
      setIsConverting(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
      <header className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-neutral-700 transition hover:text-ink focus:outline-none focus:ring-4 focus:ring-moss/20"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back
        </Link>
        <span className="text-sm font-bold text-ink">DocForge</span>
      </header>

      <section className="mt-8">
        <h1 className="text-4xl font-bold tracking-normal text-ink sm:text-5xl">{title}</h1>
        <p className="mt-3 text-base leading-7 text-neutral-700">{description}</p>
      </section>

      <form
        onSubmit={handleSubmit}
        className="mt-8 rounded-lg border border-neutral-200 bg-white/90 p-5 shadow-soft sm:p-6"
      >
        <label
          htmlFor="file"
          className="flex min-h-52 cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-neutral-300 bg-paper px-4 py-8 text-center transition hover:border-moss/60 focus-within:border-moss"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-md bg-white shadow-sm">
            <Upload className="h-6 w-6 text-moss" aria-hidden="true" />
          </span>
          <span className="text-base font-semibold text-ink">
            {file ? file.name : "Choose file"}
          </span>
          <span className="max-w-sm text-sm leading-6 text-neutral-600">
            {file ? `${formatFileSize(file.size)} selected` : helperText}
          </span>
          <input
            id="file"
            name="file"
            type="file"
            accept={accept}
            className="sr-only"
            onChange={handleFileChange}
          />
        </label>

        {file ? (
          <button
            type="button"
            onClick={clearFile}
            className="mt-4 inline-flex h-10 items-center justify-center gap-2 rounded-md border border-neutral-300 bg-white px-4 text-sm font-semibold text-neutral-700 transition hover:border-neutral-400 hover:text-ink focus:outline-none focus:ring-4 focus:ring-moss/20"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Remove file
          </button>
        ) : null}

        <button
          type="submit"
          disabled={isConverting || !file}
          className="mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-ink px-5 text-sm font-semibold text-white transition hover:bg-neutral-800 focus:outline-none focus:ring-4 focus:ring-moss/25 disabled:cursor-not-allowed disabled:bg-neutral-400"
        >
          {isConverting ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          ) : (
            <Wand2 className="h-5 w-5" aria-hidden="true" />
          )}
          Convert
        </button>

        {message ? (
          <p
            className={`mt-4 rounded-md px-3 py-2 text-sm leading-6 ${
              messageType === "error"
                ? "bg-red-50 text-red-700"
                : "bg-emerald-50 text-emerald-700"
            }`}
            role="status"
          >
            {message}
          </p>
        ) : null}

        {downloadUrl ? (
          <a
            href={downloadUrl}
            download={downloadFilename}
            className="mt-4 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-moss px-5 text-sm font-semibold text-white transition hover:bg-[#285640] focus:outline-none focus:ring-4 focus:ring-moss/25"
          >
            <Download className="h-5 w-5" aria-hidden="true" />
            {downloadLabel}
          </a>
        ) : null}
      </form>
    </main>
  );
}
