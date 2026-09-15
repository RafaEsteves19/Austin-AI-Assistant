import { useEffect, useState } from "react";

import "./history.css";

function HistoryPanel({
  apiUrl,
  open,
  onClose,
  onOpened
}) {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    if (!open) {
      return;
    }

    fetch(`${apiUrl}/api/history`)
      .then((response) => response.json())
      .then((data) => {
        setConversations(
          [...data].reverse()
        );
      })
      .catch(() => {
        setConversations([]);
      });
  }, [apiUrl, open]);

  if (!open) {
    return null;
  }

  return (
    <aside className="history-panel">

      <div className="history-header">

        <div>
          <span>HISTÓRICO</span>

          <small>
            CONVERSAS SALVAS
          </small>
        </div>

        <button
          onClick={onClose}
        >
          FECHAR
        </button>

      </div>


      <div className="history-list">

        {conversations.length === 0 && (
          <p className="history-empty">
            Nenhuma conversa encontrada.
          </p>
        )}


        {conversations.map(
          (conversation, index) => (

            <button
              className="history-item"
              key={
                conversation.arquivo ||
                index
              }
              onClick={async () => {
                try {
                  const response =
                    await fetch(
                      `${apiUrl}/api/history/open`,
                      {
                        method: "POST",

                        headers: {
                          "Content-Type":
                            "application/json"
                        },

                        body: JSON.stringify({
                          arquivo:
                            conversation.arquivo
                        })
                      }
                    );

                  if (!response.ok) {
                    return;
                  }

                  const data =
                    await response.json();

                  onOpened?.(
                    data.response
                  );

                  onClose();

                } catch {
                  // A conversa continua disponível pelo chat.
                }
              }}
            >

              <span className="history-number">
                {index + 1}
              </span>


              <div>

                <strong>
                  {conversation.titulo}
                </strong>

                <small>
                  {conversation.data}

                  {conversation.hora
                    ? ` • ${conversation.hora}`
                    : ""}
                </small>

              </div>

            </button>

          )
        )}

      </div>

    </aside>
  );
}

export default HistoryPanel;