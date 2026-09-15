import { useEffect, useRef, useState } from "react";

import "./chat.css";

function Chat({
  apiUrl,
  onStateChange,
  historyResponse
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmation, setConfirmation] = useState(false);

  const endRef = useRef(null);
  const socketRef = useRef(null);

  const onStateChangeRef = useRef(
    onStateChange
  );

  const streamingIndexRef = useRef(null);


  useEffect(() => {
    onStateChangeRef.current =
      onStateChange;
  }, [onStateChange]);


  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [messages]);


  useEffect(() => {
    if (!historyResponse) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        content: historyResponse
      }
    ]);

    onStateChangeRef.current(
      "responding"
    );
  }, [historyResponse]);


  useEffect(() => {
    fetch(`${apiUrl}/api/session`, {
      method: "POST"
    })
      .then((response) =>
        response.json()
      )
      .then((data) => {
        setMessages([
          {
            role: "assistant",
            content: data.response
          }
        ]);
      })
      .catch(() => {
        setMessages([
          {
            role: "assistant",
            content:
              "Não foi possível conectar ao Austin."
          }
        ]);
      });
  }, [apiUrl]);


  useEffect(() => {
    const websocketUrl =
      apiUrl
        .replace(/^http:/, "ws:")
        .replace(/^https:/, "wss:")
        + "/ws/chat";


    const socket = new WebSocket(
      websocketUrl
    );


    socketRef.current = socket;


    socket.onopen = () => {
      console.log(
        "WebSocket conectado."
      );
    };


    socket.onmessage = (event) => {
      const data = JSON.parse(
        event.data
      );


      if (data.type === "stream") {
        const index =
          streamingIndexRef.current;


        if (index === null) {
          return;
        }


        setMessages((current) => {
          if (!current[index]) {
            return current;
          }


          const atualizadas = [
            ...current
          ];


          atualizadas[index] = {
            ...atualizadas[index],
            content:
              atualizadas[index].content +
              (data.content || "")
          };


          return atualizadas;
        });


        onStateChangeRef.current(
          "responding"
        );

        return;
      }


      if (data.type === "done") {
        setLoading(false);


        if (data.content) {
          setMessages((current) => [
            ...current,
            {
              role: "assistant",
              content: data.content
            }
          ]);
        }


        setConfirmation(
          Boolean(
            data.requires_confirmation
          )
        );


        streamingIndexRef.current = null;


        onStateChangeRef.current(
          data.state || "idle"
        );

        return;
      }


      if (data.type === "response") {
        const index =
          streamingIndexRef.current;


        if (
          index !== null
        ) {
          setMessages((current) => {
            if (!current[index]) {
              return current;
            }


            const atualizadas = [
              ...current
            ];


            atualizadas[index] = {
              ...atualizadas[index],
              content:
                data.content || ""
            };


            return atualizadas;
          });


          streamingIndexRef.current = null;

        } else {
          setMessages((current) => [
            ...current,
            {
              role: "assistant",
              content:
                data.content || ""
            }
          ]);
        }


        setLoading(false);


        setConfirmation(
          Boolean(
            data.requires_confirmation
          )
        );


        onStateChangeRef.current(
          data.state || "idle"
        );


        return;
      }


      if (data.type === "error") {
        const errorMessage =
          data.content ||
          data.message ||
          "Ocorreu um erro.";


        const index =
          streamingIndexRef.current;


        if (
          index !== null
        ) {
          setMessages((current) => {
            if (!current[index]) {
              return current;
            }


            const atualizadas = [
              ...current
            ];


            atualizadas[index] = {
              ...atualizadas[index],
              content:
                errorMessage
            };


            return atualizadas;
          });

        } else {
          setMessages((current) => [
            ...current,
            {
              role: "assistant",
              content:
                errorMessage
            }
          ]);
        }


        setLoading(false);

        setConfirmation(false);

        streamingIndexRef.current = null;


        onStateChangeRef.current(
          "error"
        );
      }
    };


    socket.onerror = (error) => {
      console.error(
        "Erro no WebSocket:",
        error
      );
    };


    socket.onclose = (event) => {
      console.log(
        "WebSocket desconectado.",
        event.code,
        event.reason
      );


      if (
        socketRef.current === socket
      ) {
        socketRef.current = null;
      }
    };


    return () => {
      if (
        socket.readyState ===
          WebSocket.OPEN ||
        socket.readyState ===
          WebSocket.CONNECTING
      ) {
        socket.close();
      }


      if (
        socketRef.current === socket
      ) {
        socketRef.current = null;
      }
    };
  }, [apiUrl]);


  function sendMessage(
    text = input
  ) {
    const message =
      text.trim();


    if (
      !message ||
      loading
    ) {
      return;
    }


    const socket =
      socketRef.current;


    if (
      !socket ||
      socket.readyState !==
        WebSocket.OPEN
    ) {
      console.error(
        "WebSocket ainda não está conectado."
      );


      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Não foi possível estabelecer comunicação com o Austin."
        }
      ]);


      onStateChangeRef.current(
        "error"
      );


      return;
    }


    const assistantIndex =
      messages.length + 1;


    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: message
      },
      {
        role: "assistant",
        content: ""
      }
    ]);


    streamingIndexRef.current =
      assistantIndex;


    setInput("");

    setLoading(true);

    setConfirmation(false);


    onStateChangeRef.current(
      "thinking"
    );


    socket.send(
      JSON.stringify({
        message
      })
    );
  }


  return (
    <section className="chat">

      <div className="chat-header">

        <div>

          <span>
            CONVERSA
          </span>

          <small>
            CANAL PRINCIPAL
          </small>

        </div>

        <span className="chat-indicator" />

      </div>


      <div className="messages">

        {messages.map(
          (message, index) => (

            <article
              className={`message ${message.role}`}
              key={index}
            >

              <span className="message-label">

                {message.role === "assistant"
                  ? "AUSTIN"
                  : "VOCÊ"}

              </span>


              <p>
                {message.content}
              </p>

            </article>

          )
        )}


        {loading &&
          streamingIndexRef.current !== null &&
          messages[
            streamingIndexRef.current
          ]?.content === "" && (

            <article className="message assistant">

              <span className="message-label">
                AUSTIN
              </span>

              <div className="thinking">

                <span />
                <span />
                <span />

              </div>

            </article>

          )}


        <div ref={endRef} />

      </div>


      {confirmation && (

        <div className="confirmation">

          <button
            onClick={() =>
              sendMessage("sim")
            }
          >
            SIM
          </button>


          <button
            onClick={() =>
              sendMessage("não")
            }
          >
            NÃO
          </button>

        </div>

      )}


      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();

          sendMessage();
        }}
      >

        <input
          value={input}

          onChange={(event) =>
            setInput(
              event.target.value
            )
          }

          placeholder="Digite uma instrução..."

          disabled={loading}

        />


        <button
          type="submit"

          disabled={
            loading ||
            !input.trim()
          }
        >
          ENVIAR
        </button>

      </form>

    </section>
  );
}

export default Chat;