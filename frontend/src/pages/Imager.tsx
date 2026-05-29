import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { RiImageLine, RiLoader4Line, RiSparklingLine, RiDownload2Line } from 'react-icons/ri';

import { generateImagerImage } from '@services/videoService';
import type { ImagerGenerateResponse, ImagerModel } from '@/types';

const MODEL_OPTIONS: Array<{
  value: ImagerModel;
  label: string;
  hint: string;
}> = [
  {
    value: 'flux_schnell',
    label: 'FLUX.1-schnell',
    hint: 'Mais rapido. Ideal para iterar prompt e gerar em poucos segundos.',
  },
  {
    value: 'flux_dev',
    label: 'FLUX.1-dev',
    hint: 'Mais qualidade. Mais lento e mais pesado para CPU/GPU.',
  },
];

export default function Imager() {
  const [prompt, setPrompt] = useState('a futuristic city at sunset, cinematic lighting');
  const [model, setModel] = useState<ImagerModel>('flux_schnell');
  const [seed, setSeed] = useState('');
  const [result, setResult] = useState<ImagerGenerateResponse | null>(null);

  const selectedModel = useMemo(
    () => MODEL_OPTIONS.find((item) => item.value === model) ?? MODEL_OPTIONS[0],
    [model]
  );

  const mutation = useMutation({
    mutationFn: generateImagerImage,
    onSuccess: (data) => {
      setResult(data);
      toast.success('Imagem gerada com sucesso');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Falha ao gerar imagem');
    },
  });

  const handleGenerate = () => {
    const trimmed = prompt.trim();
    if (!trimmed) {
      toast.error('Digite um prompt para gerar a imagem');
      return;
    }

    mutation.mutate({
      prompt: trimmed,
      model,
      width: 1024,
      height: 1024,
      seed: seed.trim() ? Number(seed) : undefined,
    });
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 xl:grid-cols-[460px_1fr] gap-6">
      <section className="card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-accent/10 flex items-center justify-center border border-accent/20">
            <RiSparklingLine className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-display font-bold text-text-primary">Imager</h1>
            <p className="text-sm text-text-secondary">
              Gere imagens standalone via FLUX a partir de um prompt livre.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-text-secondary">Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={7}
            className="input min-h-40 resize-y"
            placeholder="Descreva a imagem que voce quer gerar..."
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-text-secondary">Modelo</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as ImagerModel)}
              className="input"
            >
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-text-muted">{selectedModel.hint}</p>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-text-secondary">Seed opcional</label>
            <input
              value={seed}
              onChange={(e) => setSeed(e.target.value.replace(/[^\d]/g, ''))}
              className="input"
              placeholder="Ex: 42"
            />
            <p className="text-xs text-text-muted">
              Use seed para reproduzir o mesmo resultado quando estiver no FLUX.1-dev.
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-background-secondary/60 p-4 text-sm text-text-secondary">
          O primeiro uso baixa os pesos do modelo e pode demorar bastante, principalmente no
          FLUX.1-dev.
        </div>

        <button
          type="button"
          onClick={handleGenerate}
          disabled={mutation.isPending}
          className="btn-primary h-12 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {mutation.isPending ? (
            <>
              <RiLoader4Line className="w-4 h-4 animate-spin" />
              Gerando imagem...
            </>
          ) : (
            <>
              <RiImageLine className="w-4 h-4" />
              Gerar com {selectedModel.label}
            </>
          )}
        </button>
      </section>

      <section className="card p-6 flex flex-col gap-4 min-h-[720px]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-display font-semibold text-text-primary">Preview</h2>
            <p className="text-sm text-text-secondary">
              A imagem gerada fica salva em exports/imager e pode ser reutilizada depois.
            </p>
          </div>
          {result && (
            <a
              href={result.image_url}
              download
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border text-sm text-text-primary hover:bg-background-hover transition-colors"
            >
              <RiDownload2Line className="w-4 h-4" />
              Baixar
            </a>
          )}
        </div>

        <div className="flex-1 rounded-[28px] border border-border bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_45%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] overflow-hidden flex items-center justify-center p-6">
          {result ? (
            <img
              src={result.image_url}
              alt="Imagem gerada"
              className="max-h-full max-w-full rounded-[24px] object-contain shadow-2xl"
            />
          ) : (
            <div className="max-w-md text-center flex flex-col items-center gap-4 text-text-secondary">
              <div className="w-16 h-16 rounded-3xl bg-accent/10 border border-accent/20 flex items-center justify-center">
                <RiSparklingLine className="w-7 h-7 text-accent" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-text-primary">Nenhuma imagem gerada ainda</h3>
                <p className="text-sm">
                  Escreva um prompt, escolha o modelo FLUX e gere uma imagem independente do
                  fluxo de video.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}