import { useId, useMemo, useRef, useState } from "react";
import { searchCatalog, type CatalogIndex, type SearchHit } from "../domain/catalogIndex";

interface Props {
  index: CatalogIndex | null;
  onPickStation: (stationId: string) => void;
  onPickLine: (lineId: string) => void;
}

/**
 * Búsqueda por estación y línea, con y sin tilde. Teclado completo: flechas
 * recorren, Intro selecciona, Escape cierra sin perder el contexto actual.
 */
export function SearchBox({ index, onPickStation, onPickLine }: Props) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  // Los resultados se derivan del texto en el render: no hay estado
  // duplicado que pueda quedar desfasado respecto a la consulta.
  const hits = useMemo(
    () => (index === null || query.trim() === "" ? [] : searchCatalog(index, query)),
    [index, query],
  );
  const open = !dismissed && query.trim() !== "";
  const active = hits.length === 0 ? 0 : Math.min(cursor, hits.length - 1);

  function pick(hit: SearchHit) {
    if (hit.kind === "station") onPickStation(hit.id);
    else onPickLine(hit.id);
    setQuery("");
    setCursor(0);
    setDismissed(false);
  }

  return (
    <div className="searchbox">
      <input
        ref={inputRef}
        type="search"
        value={query}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-label="Buscar estación o línea"
        placeholder="Buscar estación o línea"
        autoComplete="off"
        onChange={(event) => {
          setQuery(event.target.value);
          setCursor(0);
          setDismissed(false);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            setQuery("");
            setDismissed(true);
            return;
          }
          if (!open || hits.length === 0) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setCursor((active + 1) % hits.length);
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setCursor((active - 1 + hits.length) % hits.length);
          } else if (event.key === "Enter") {
            event.preventDefault();
            pick(hits[active]);
          }
        }}
      />
      {open && (
        <ul className="search-results" id={listId} role="listbox">
          {hits.length === 0 ? (
            <li className="search-empty">Sin coincidencias en el catálogo</li>
          ) : (
            hits.map((hit, position) => (
              <li key={`${hit.kind}:${hit.id}`} role="option" aria-selected={position === active}>
                <button
                  type="button"
                  className={position === active ? "search-hit is-active" : "search-hit"}
                  onMouseEnter={() => setCursor(position)}
                  onClick={() => pick(hit)}
                >
                  <span>{hit.label}</span>
                  <small>{hit.detail}</small>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
