import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Image-to-3D",
  description: "Genera modelli .glb con scheletro da immagini su GPU locale",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className="antialiased min-h-screen bg-zinc-950 text-zinc-100">
        {children}
      </body>
    </html>
  );
}
