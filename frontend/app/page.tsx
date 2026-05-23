import Link from "next/link";
import { ArrowRight, FileText, Image, Type } from "lucide-react";

const features = [
  {
    title: "Word to PDF",
    description: "Convert .doc and .docx files.",
    meta: "DOC, DOCX",
    href: "/word-to-pdf",
    icon: FileText,
    color: "text-moss",
  },
  {
    title: "Image to PDF",
    description: "Convert JPG and PNG images.",
    meta: "JPG, PNG",
    href: "/image-to-pdf",
    icon: Image,
    color: "text-coral",
  },
  {
    title: "Text to PDF",
    description: "Paste text and create a PDF.",
    meta: "Plain text",
    href: "/text-to-pdf",
    icon: Type,
    color: "text-skyline",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-6 sm:px-8 lg:py-10">
      <header className="flex items-center justify-between">
        <Link href="/" className="text-lg font-bold text-ink">
          DocForge
        </Link>
      </header>

      <section className="flex flex-1 flex-col justify-center gap-8 py-10">
        <div className="max-w-2xl">
          <p className="mb-3 text-sm font-semibold uppercase text-moss">
            Simple PDF tools
          </p>
          <h1 className="text-5xl font-bold leading-tight text-ink sm:text-6xl">
            DocForge
          </h1>
          <p className="mt-4 text-lg leading-8 text-neutral-700">
            Convert documents, images, and text to PDF.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;

            return (
              <Link
                key={feature.href}
                href={feature.href}
                className="group flex min-h-56 flex-col rounded-lg border border-neutral-200 bg-white/85 p-5 shadow-soft transition hover:-translate-y-1 hover:border-neutral-300 hover:bg-white focus:outline-none focus:ring-4 focus:ring-moss/20"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-neutral-100">
                    <Icon className={`h-6 w-6 ${feature.color}`} aria-hidden="true" />
                  </div>
                  <span className="rounded-full border border-neutral-200 px-3 py-1 text-xs font-semibold text-neutral-600">
                    {feature.meta}
                  </span>
                </div>
                <h2 className="mt-5 text-xl font-semibold text-ink">{feature.title}</h2>
                <p className="mt-2 text-sm leading-6 text-neutral-600">
                  {feature.description}
                </p>
                <div className="mt-auto flex items-center gap-2 pt-6 text-sm font-semibold text-moss">
                  Start
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" aria-hidden="true" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}
