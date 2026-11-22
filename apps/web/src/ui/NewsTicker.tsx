import { useEffect, useState } from "react";

export interface NewsItem {
  id: string;
  text: string;
  onOpen?: () => void;
}

interface Props {
  items: NewsItem[];
  paused: boolean;
  onTogglePause: () => void;
  reducedMotion: boolean;
}

const ROTATE_MS = 9_000;

/**
 * Cinta de novedades progresiva: avanza a velocidad de lectura, se puede
 * pausar (la pausa persiste en la sesión), se puede ver entera como lista y
 * **no** es un carrusel obligatorio. No anuncia continuamente a lectores de
 * pantalla: la región es `polite` y solo cambia cuando cambia el aviso.
 */
export function NewsTicker({ items, paused, onTogglePause, reducedMotion }: Props) {
  const [cursor, setCursor] = useState(0);
  const [expanded, setExpanded] = useState(false);
  // La posición se acota en el render: si la lista encoge, no hace falta un
  // efecto que corrija el estado después de pintar.
  const position = items.length === 0 ? 0 : cursor % items.length;

  useEffect(() => {
    if (paused || reducedMotion || items.length < 2) return;
    const timer = window.setInterval(() => {
      if (document.hidden) return;
      setCursor((current) => (current + 1) % items.length);
    }, ROTATE_MS);
    return () => window.clearInterval(timer);
  }, [paused, reducedMotion, items.length]);

  const current = items[position];

  return (
    <footer className="ticker">
      <b className="mono">Novedades</b>
      {current === undefined ? (
        <p className="ticker__event ticker__event--empty">Sin novedades en el snapshot vigente.</p>
      ) : (
        <button
          type="button"
          className="ticker__event"
          onClick={current.onOpen}
          disabled={current.onOpen === undefined}
        >
          {current.text}
        </button>
      )}
      <span className="ticker__count mono">
        {items.length === 0 ? "0" : `${position + 1}/${items.length}`}
      </span>
      <button
        type="button"
        className="ticker__button"
        onClick={onTogglePause}
        aria-pressed={paused}
        disabled={items.length < 2}
      >
        {paused ? "Reanudar" : "Pausar"}
      </button>
      <button
        type="button"
        className="ticker__button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        disabled={items.length === 0}
      >
        {expanded ? "Ocultar lista" : "Ver lista"}
      </button>
      <p className="visually-hidden" role="status">
        {current?.text ?? ""}
      </p>
      {expanded && (
        <ul className="ticker__list">
          {items.map((item) => (
            <li key={item.id}>
              <button type="button" onClick={item.onOpen} disabled={item.onOpen === undefined}>
                {item.text}
              </button>
            </li>
          ))}
        </ul>
      )}
    </footer>
  );
}
