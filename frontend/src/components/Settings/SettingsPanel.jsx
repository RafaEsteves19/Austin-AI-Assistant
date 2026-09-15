import "./settings.css";


function SettingsPanel({
  open,
  onClose,
  apiOnline,
  modelMode,
  currentModel,
  modelAvailability,
  onModelModeChange,
  onNewSession
}) {

  if (!open) {
    return null;
  }


  function selecionarModo(modo) {

    if (modo === modelMode) {
      return;
    }

    onModelModeChange(
      modo
    );

  }


  function nomeModelo(modelo) {

    if (modelo === "groq") {
      return "GROQ";
    }

    if (modelo === "ollama") {
      return "OLLAMA";
    }

    return "—";

  }


  return (

    <aside className="settings-panel">

      <div className="settings-header">

        <div>

          <span>
            CONFIGURAÇÕES
          </span>

          <small>
            SISTEMA A.U.S.T.I.N
          </small>

        </div>


        <button
          onClick={onClose}
        >
          FECHAR
        </button>

      </div>


      <div className="settings-content">

        <div className="setting-row">

          <span>
            Servidor local
          </span>

          <strong>
            {apiOnline
              ? "ONLINE"
              : "OFFLINE"}
          </strong>

        </div>


        <div className="setting-row">

          <span>
            Interface
          </span>

          <strong>
            REACT + VITE
          </strong>

        </div>


        <div className="setting-row">

          <span>
            Renderização
          </span>

          <strong>
            THREE.JS
          </strong>

        </div>


        <div className="model-setting">

          <div className="model-setting-title">

            <span>
              Modelo de IA
            </span>

            <small>
              SELECIONE O MODO
            </small>

          </div>


          <div className="model-mode-buttons">

            <button
              className={
                modelMode === "groq"
                  ? "active"
                  : ""
              }
              onClick={() => {
                selecionarModo("groq");
              }}
            >
              API
            </button>


            <button
              className={
                modelMode === "auto"
                  ? "active"
                  : ""
              }
              onClick={() => {
                selecionarModo("auto");
              }}
            >
              AUTO
            </button>


            <button
              className={
                modelMode === "ollama"
                  ? "active"
                  : ""
              }
              onClick={() => {
                selecionarModo("ollama");
              }}
            >
              LOCAL
            </button>

          </div>


          <div className="model-status">

            <div className="model-status-row">

              <span>
                Modo
              </span>

              <strong>
                {modelMode.toUpperCase()}
              </strong>

            </div>


            <div className="model-status-row">

              <span>
                Modelo atual
              </span>

              <strong>
                {nomeModelo(
                  currentModel
                )}
              </strong>

            </div>


            <div className="model-status-row">

              <span>
                API
              </span>

              <strong
                className={
                  modelAvailability?.groq
                    ? "available"
                    : "unavailable"
                }
              >
                {modelAvailability?.groq
                  ? "DISPONÍVEL"
                  : "INDISPONÍVEL"}
              </strong>

            </div>


            <div className="model-status-row">

              <span>
                LOCAL
              </span>

              <strong
                className={
                  modelAvailability?.ollama
                    ? "available"
                    : "unavailable"
                }
              >
                {modelAvailability?.ollama
                  ? "DISPONÍVEL"
                  : "INDISPONÍVEL"}
              </strong>

            </div>

          </div>

        </div>


        <button
          className="new-session"
          onClick={onNewSession}
        >
          NOVA SESSÃO
        </button>

      </div>

    </aside>

  );

}


export default SettingsPanel;