"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2, Type, Wand2 } from "lucide-react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const maxTextSize = 10 * 1024 * 1024;

export function TextConverterForm() {
  const [text, setText] = useState("");
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim()) {
      setMessage("Enter text first.");
      setMessageType("error");
      return;
    }
    if (new TextEncoder().encode(text).length > maxTextSize) {
      setMessage("Text size must be 10MB or less.");
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

    try {
      const response = await fetch(`${apiUrl}/api/text-to-pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail ?? "Conversion failed.");
      }

      const blob = await response.blob();
      setDownloadUrl(URL.createObjectURL(blob));
      setMessage("PDF is ready.");
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
        <h1 className="text-4xl font-bold tracking-normal text-ink sm:text-5xl">Text to PDF</h1>
        <p className="mt-3 text-base leading-7 text-neutral-700">
          Paste text and create a PDF.
        </p>
      </section>

      <form
        onSubmit={handleSubmit}
        className="mt-8 rounded-lg border border-neutral-200 bg-white/90 p-5 shadow-soft sm:p-6"
      >
        <label htmlFor="text" className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
          <Type className="h-4 w-4 text-skyline" aria-hidden="true" />
          Text
        </label>
        <textarea
          id="text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={12}
          className="w-full resize-y rounded-lg border border-neutral-300 bg-paper px-4 py-3 text-base leading-7 text-ink outline-none transition placeholder:text-neutral-400 focus:border-skyline focus:ring-4 focus:ring-skyline/15"
          placeholder="Paste your text here"
        />
        <div className="mt-2 flex justify-between gap-4 text-xs font-medium text-neutral-500">
          <span>{text.trim() ? `${text.length} characters` : "No text entered"}</span>
          <span>Limit: 10MB</span>
        </div>

        <button
          type="submit"
          disabled={isConverting || !text.trim()}
          className="mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-ink px-5 text-sm font-semibold text-white transition hover:bg-neutral-800 focus:outline-none focus:ring-4 focus:ring-skyline/25 disabled:cursor-not-allowed disabled:bg-neutral-400"
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
            download="converted.pdf"
            className="mt-4 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-moss px-5 text-sm font-semibold text-white transition hover:bg-[#285640] focus:outline-none focus:ring-4 focus:ring-moss/25"
          >
            <Download className="h-5 w-5" aria-hidden="true" />
            Download PDF
          </a>
        ) : null}
      </form>
    </main>
  );
}
