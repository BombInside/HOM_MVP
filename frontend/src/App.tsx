import "./i18n";
import Router from "./router"; // ✅ импорт по умолчанию, а не { router }

function App() {
  // ✅ просто рендерим Router
  return <Router />;
}

export default App;
