import { useState } from 'react';
import { RiImageLine, RiDownload2Line, RiLoader4Line, RiZoomInLine, RiCloseLine } from 'react-icons/ri';
import { getGeneratedImageUrl } from '@/services/videoService';

interface Props {
  readonly projectId: string;
  readonly images: string[];
  readonly isGenerating?: boolean;
}

export default function GeneratedImages({ projectId, images, isGenerating }: Props) {
  const [lightbox, setLightbox] = useState<string | null>(null);

  // Extract only the filename from the full path returned by the backend
  const toUrl = (pathOrUrl: string) => {
    const filename = pathOrUrl.replaceAll('\\', '/').split('/').pop() ?? '';
    return getGeneratedImageUrl(projectId, filename);
  };

  if (isGenerating) {
    return (
      <div className="card p-5 flex flex-col gap-3">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <RiImageLine className="w-4 h-4 text-accent" />
          Imagens de Cena
        </h3>
        <div className="grid grid-cols-5 gap-2">
          {Array.from({ length: 5 }, (_, i) => (
            <div
              key={`skeleton-img-${i + 1}`}
              className="aspect-[9/16] rounded-lg bg-background-secondary border border-border flex items-center justify-center"
            >
              <RiLoader4Line className="w-4 h-4 text-text-muted animate-spin" />
            </div>
          ))}
        </div>
        <p className="text-xs text-text-muted text-center">Gerando imagens com DALL-E 3…</p>
      </div>
    );
  }

  if (!images || images.length === 0) return null;

  return (
    <>
      <div className="card p-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <RiImageLine className="w-4 h-4 text-accent" />
            Imagens de Cena
            <span className="badge-accent">{images.length}</span>
          </h3>
        </div>

        <div className="grid grid-cols-5 gap-2">
          {images.map((img, i) => {
            const url = toUrl(img);
            return (
              <div key={img} className="group relative aspect-[9/16] rounded-lg overflow-hidden border border-border bg-background-secondary">
                <img
                  src={url}
                  alt={`Cena ${i + 1}`}
                  className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                  loading="lazy"
                />
                {/* Overlay on hover */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-200 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                  <button
                    type="button"
                    onClick={() => setLightbox(url)}
                    className="w-7 h-7 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center"
                    title="Ampliar"
                  >
                    <RiZoomInLine className="w-3.5 h-3.5 text-white" />
                  </button>
                  <a
                    href={url}
                    download={`scene_${i + 1}.png`}
                    className="w-7 h-7 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center"
                    title="Baixar"
                  >
                    <RiDownload2Line className="w-3.5 h-3.5 text-white" />
                  </a>
                </div>
                <span className="absolute bottom-1 left-1 text-[10px] text-white/70 font-medium bg-black/40 rounded px-1">
                  {i + 1}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Lightbox */}
      {lightbox && (
        <dialog
          open
          aria-label="Imagem ampliada"
          className="fixed inset-0 z-50 m-0 max-w-none w-full h-full bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 border-0"
        >
          <button
            type="button"
            className="absolute inset-0 w-full h-full cursor-default"
            aria-label="Fechar"
            onClick={() => setLightbox(null)}
            onKeyDown={(e) => e.key === 'Escape' && setLightbox(null)}
          />
          <div className="relative z-10">
            <img
              src={lightbox}
              alt="Cena ampliada"
              className="max-h-[90vh] max-w-sm rounded-xl shadow-2xl"
            />
            <button
              type="button"
              onClick={() => setLightbox(null)}
              className="absolute -top-3 -right-3 w-7 h-7 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center"
              aria-label="Fechar"
            >
              <RiCloseLine className="w-4 h-4 text-white" />
            </button>
          </div>
        </dialog>
      )}
    </>
  );
}

