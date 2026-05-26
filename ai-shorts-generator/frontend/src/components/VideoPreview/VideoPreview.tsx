import ReactPlayer from 'react-player';
import { useState } from 'react';
import {
  RiPlayLine,
  RiPauseLine,
  RiVolumeUpLine,
  RiVolumeMuteLine,
  RiDownload2Line,
  RiFullscreenLine,
} from 'react-icons/ri';
import { getThumbnail, downloadExport } from '@/services/videoService';

interface Props {
  projectId: string;
  videoUrl?: string;
  thumbnailUrl?: string;
}

export default function VideoPreview({ projectId, videoUrl, thumbnailUrl }: Props) {
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [progress, setProgress] = useState(0);

  const thumb = thumbnailUrl ?? getThumbnail(projectId);

  return (
    <div className="flex flex-col gap-3">
      {/* Player */}
      <div
        className="relative rounded-xl overflow-hidden bg-black"
        style={{ aspectRatio: '9/16', maxHeight: 480 }}
      >
        {videoUrl ? (
          <ReactPlayer
            url={videoUrl}
            playing={playing}
            muted={muted}
            width="100%"
            height="100%"
            style={{ position: 'absolute', top: 0, left: 0 }}
            onProgress={({ played }) => setProgress(played * 100)}
            light={thumb}
            playIcon={
              <button className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center border border-white/15">
                <RiPlayLine className="w-6 h-6 text-white ml-0.5" />
              </button>
            }
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-text-muted text-sm">
            Sem preview disponível
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
      </div>

      {/* Progress bar */}
      {videoUrl && (
        <div className="h-0.5 rounded-full bg-background-hover overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Controls */}
      {videoUrl && (
        <div className="flex items-center gap-1">
          <button className="btn-ghost px-2.5 py-1.5" onClick={() => setPlaying((v) => !v)}>
            {playing ? <RiPauseLine className="w-4 h-4" /> : <RiPlayLine className="w-4 h-4" />}
          </button>
          <button className="btn-ghost px-2.5 py-1.5" onClick={() => setMuted((v) => !v)}>
            {muted
              ? <RiVolumeMuteLine className="w-4 h-4" />
              : <RiVolumeUpLine className="w-4 h-4" />
            }
          </button>
          <div className="flex-1" />
          <a href={downloadExport(projectId)} download className="btn-secondary text-xs gap-1.5">
            <RiDownload2Line className="w-3.5 h-3.5" />
            Download
          </a>
          <button className="btn-ghost px-2.5 py-1.5">
            <RiFullscreenLine className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
