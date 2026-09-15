import { useEffect, useState } from "react";

import AustinSphere from "./components/Sphere/AustinSphere";
import Chat from "./components/Chat/Chat";
import HistoryPanel from "./components/History/HistoryPanel";
import SettingsPanel from "./components/Settings/SettingsPanel";

import "./styles/app.css";


const API_URL = "http://127.0.0.1:8000";


function App() {

  const [state, setState] = useState("idle");

  const [historyOpen, setHistoryOpen] = useState(false);

  const [online, setOnline] = useState(false);

  const [settingsOpen, setSettingsOpen] = useState(false);

  const [historyResponse, setHistoryResponse] = useState(null);

  const [modelMode, setModelMode] = useState("auto");

  const [currentModel, setCurrentModel] = useState(null);

  const [modelAvailability, setModelAvailability] = useState({
    groq: false,
    ollama: false
  });


  useEffect(() => {

    fetch(`${API_URL}/api/health`)

      .then((response) => {

        if (!response.ok) {
          throw new Error(
            "Servidor indisponível."
          );
        }

        setOnline(true);

      })

      .catch(() => {

        setOnline(false);

      });


    carregarStatusModelo();

  }, []);


  async function carregarStatusModelo() {

    try {

      const response = await fetch(
        `${API_URL}/api/model/status`
      );


      if (!response.ok) {

        throw new Error(
          "Não foi possível obter o status do modelo."
        );

      }


      const data = await response.json();


      setModelMode(
        data.mode
      );


      setCurrentModel(
        data.model
      );


      setModelAvailability(
        data.available || {
          groq: false,
          ollama: false
        }
      );


    } catch (error) {

      console.error(
        "Erro ao obter status do modelo:",
        error
      );

    }

  }


  async function alterarModoModelo(modo) {

    try {

      const response = await fetch(
        `${API_URL}/api/model/mode`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            mode: modo
          })
        }
      );


      if (!response.ok) {

        throw new Error(
          "Não foi possível alterar o modo do modelo."
        );

      }


      const data = await response.json();


      setModelMode(
        data.status.mode
      );


      setCurrentModel(
        data.status.model
      );


      setModelAvailability(
        data.status.available || {
          groq: false,
          ollama: false
        }
      );


    } catch (error) {

      console.error(
        "Erro ao alterar modelo:",
        error
      );

    }

  }


  function handleStateChange(nextState) {

    setState(
      nextState
    );

  }


  return (

    <div>

      <header className="topbar">

        <div className="brand">

          <span className="brand-mark">
            A
          </span>

          <div>

            <strong>
              A.U.S.T.I.N
            </strong>

            <span>
              AI SYSTEM
            </span>

          </div>

        </div>


        <div className="top-actions">

          <button
            className="top-action"
            onClick={() => setSettingsOpen(true)}
          >
            CONFIG
          </button>


          <div className="system-status">

            <span
              className={`status-dot ${
                online
                  ? "online"
                  : "offline"
              }`}
            />


            <span>

              {online
                ? "ONLINE"
                : "OFFLINE"}

            </span>

          </div>

        </div>

      </header>


      <main>

        <section className="main-interface">

          <div className="sphere-area">

            <AustinSphere
              state={state}
            />


            <div className="sphere-label">

              <span>
                AUSTIN
              </span>

              <small>
                {state.toUpperCase()}
              </small>

            </div>

          </div>


          <Chat
            apiUrl={API_URL}
            onStateChange={handleStateChange}
            historyResponse={historyResponse}
          />

        </section>

      </main>


      <button
        className="history-toggle"
        onClick={() => setHistoryOpen(true)}
      >
        HISTÓRICO
      </button>


      <HistoryPanel
        apiUrl={API_URL}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onOpened={(data) => {
          setHistoryResponse(data);
        }}
      />


      <SettingsPanel
        open={settingsOpen}

        apiOnline={online}

        modelMode={modelMode}

        currentModel={currentModel}

        modelAvailability={modelAvailability}

        onModelModeChange={
          alterarModoModelo
        }

        onClose={() => setSettingsOpen(false)}

        onNewSession={() => {
          window.location.reload();
        }}
      />

    </div>

  );

}


export default App;