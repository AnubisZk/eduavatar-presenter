// Top-level React state container and page switcher for the studio workflow.
import { useState } from "react";

import Layout from "./components/Layout.jsx";
import CreatePage from "./pages/CreatePage.jsx";
import HomePage from "./pages/HomePage.jsx";
import OutputPage from "./pages/OutputPage.jsx";
import PreviewPage from "./pages/PreviewPage.jsx";

const initialStudio = {
  currentStep: 1,
  consent: {
    userName: "",
    imagePermission: false,
    voicePermission: false,
    purposeAcknowledgement: false,
    misuseAcknowledgement: false,
  },
  files: {
    avatar: null,
    voice: null,
    presentation: null,
  },
  script: "",
  targetLanguage: "English",
  voiceProvider: "edge",
  uploadResult: null,
  scriptResult: null,
  voiceResult: null,
  avatarResult: null,
  outputResult: null,
  status: "",
  statusType: "success",
};

export default function App() {
  const [activePage, setActivePage] = useState("home");
  const [studio, setStudio] = useState(initialStudio);

  const page =
    activePage === "create" ? (
      <CreatePage studio={studio} setStudio={setStudio} setActivePage={setActivePage} />
    ) : activePage === "preview" ? (
      <PreviewPage studio={studio} setStudio={setStudio} setActivePage={setActivePage} />
    ) : activePage === "output" ? (
      <OutputPage studio={studio} setActivePage={setActivePage} />
    ) : (
      <HomePage setActivePage={setActivePage} />
    );

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {page}
    </Layout>
  );
}
