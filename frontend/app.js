(() => {
  const { useState, useEffect, useRef } = React;

  const WS_URL = "ws://localhost:8000/ws/chat";

  function renderMarkdown(mdText) {
    try {
      const html = marked.parse(mdText ?? "", { breaks: true, gfm: true });
      return DOMPurify.sanitize(html);
    } catch (e) {
      return (mdText ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;");
    }
  }

  function SendIcon() {
    return React.createElement(
      "svg",
      {
        className: "icon",
        viewBox: "0 0 24 24",
        fill: "none",
        xmlns: "http://www.w3.org/2000/svg",
        "aria-hidden": "true",
      },
      React.createElement("path", {
        d: "M12 5v14",
        stroke: "currentColor",
        strokeWidth: "1.6",
        strokeLinecap: "round",
      }),
      React.createElement("path", {
        d: "M8 9l4-4 4 4",
        stroke: "currentColor",
        strokeWidth: "1.6",
        strokeLinecap: "round",
        strokeLinejoin: "round",
      })
    );
  }

  function ChatLayout(props) {
    return React.createElement(
      "div",
      { className: "chat-layout" },
      props.sidebar,
      React.createElement(
        "main",
        { className: "chat-main" },
        props.messages,
        props.input
      )
    );
  }

  function Sidebar(props) {
    const { onSuggestionClick, lastError, isConnecting, isSending, onNewChat } =
      props;

    function SuggestionChips() {
      const suggestions = [
        "ما هي متطلبات الشفافية في أنظمة الذكاء الاصطناعي؟",
        "ما هو إجمالي المبيعات حسب المنطقة؟",
        "Generate a compliance report",
        "Top 10 products by profit",
      ];
      return React.createElement(
        "div",
        { className: "chips" },
        suggestions.map((s) =>
          React.createElement(
            "button",
            {
              key: s,
              className: "chip",
              type: "button",
              onClick: () => onSuggestionClick(s),
              disabled: isConnecting || isSending,
              title: "Insert suggestion",
            },
            s
          )
        )
      );
    }

    return React.createElement(
      "aside",
      { className: "sidebar" },
      React.createElement(
        "div",
        { className: "sidebar-header" },
        React.createElement(
          "button",
          {
            type: "button",
            className: "btn new-chat",
            onClick: onNewChat,
          },
          "New chat"
        )
      ),
      React.createElement(
        "div",
        { className: "card" },
        React.createElement("h4", null, "Quick prompts"),
        React.createElement(SuggestionChips, null),
        lastError
          ? React.createElement(
              "p",
              {
                style: {
                  marginTop: "10px",
                  color: "rgba(248,113,113,0.95)",
                  fontSize: "12px",
                },
              },
              lastError
            )
          : null
      ),
      React.createElement(
        "div",
        { className: "sidebar-footer" },
        React.createElement(
          "div",
          { className: "sidebar-status" },
          React.createElement("span", {
            className:
              "status-dot " + (isConnecting ? "status-dot--bad" : "status-dot--ok"),
          }),
          React.createElement(
            "span",
            { className: "sidebar-status-text" },
            isConnecting ? "Connecting" : "Online"
          )
        )
      )
    );
  }

  function MessageBubble(props) {
    const { role, isStreaming, html, text } = props;

    const isUser = role === "user";
    const bubbleClass =
      "bubble " +
      (isUser ? "user" : "assistant") +
      (isStreaming ? " bubble--streaming" : "");

    return React.createElement(
      "div",
      { className: "row " + (isUser ? "user" : "assistant") },
      !isUser
        ? React.createElement("div", { className: "avatar bot" }, "AI")
        : null,
      React.createElement(
        "div",
        { className: bubbleClass },
        !isUser && html
          ? React.createElement("div", {
              className: "md",
              dangerouslySetInnerHTML: { __html: html },
            })
          : React.createElement(
              "div",
              { className: isStreaming ? "md-stream" : "plain" },
              text
            )
      ),
      isUser ? React.createElement("div", { className: "avatar user" }, "You") : null
    );
  }

  function MessageList(props) {
    const { messages, streamBuffer, isSending, messagesEndRef } = props;

    return React.createElement(
      "div",
      { className: "messages" },
      React.createElement(
        "div",
        { className: "chat-inner" },
        messages.map((m) =>
          React.createElement(MessageBubble, {
            key: m.id,
            role: m.role,
            text: m.text,
            html: m.role === "assistant" ? renderMarkdown(m.text) : "",
            isStreaming: false,
          })
        ),

        streamBuffer
          ? React.createElement(MessageBubble, {
              key: "__stream__",
              role: "assistant",
              text: streamBuffer,
              html: "",
              isStreaming: true,
            })
          : null,

        isSending
          ? React.createElement(
              "div",
              { className: "row assistant" },
              React.createElement("div", { className: "avatar bot" }, "AI"),
              React.createElement(
                "div",
                { className: "bubble assistant bubble--streaming" },
                React.createElement(
                  "div",
                  { className: "typing" },
                  React.createElement("span", null),
                  React.createElement("span", null),
                  React.createElement("span", null)
                )
              )
            )
          : null,

        React.createElement("div", { ref: messagesEndRef })
      )
    );
  }

  function ChatInput(props) {
    const { input, onChange, onSubmit, onKeyDown, textareaRef, isConnecting, isSending } =
      props;

    return React.createElement(
      "div",
      { className: "composer" },
      React.createElement(
        "form",
        { className: "chat-inner composer-form", onSubmit },
        React.createElement(
          "div",
          { className: "composer-inner" },
          React.createElement("textarea", {
            ref: textareaRef,
            value: input,
            placeholder: "Ask anything",
            dir: "auto",
            onChange,
            onKeyDown,
            disabled: isConnecting,
            rows: 1,
          }),
          React.createElement(
            "button",
            {
              className: "send-btn",
              type: "submit",
              disabled: isConnecting || isSending || !input.trim(),
              title: "Send",
              "aria-label": "Send message",
            },
            React.createElement(SendIcon, null)
          )
        )
      )
    );
  }

  function ChatApp() {
    const [messages, setMessages] = useState([
      {
        id: 0,
        role: "assistant",
        text:
          "مرحباً! أنا مساعد تحليلات الأعمال والامتثال لسدايا.\n\n" +
          "- اسألني عن بيانات المبيعات والأرباح\n" +
          "- أو اسألني عن مبادئ أخلاقيات الذكاء الاصطناعي (سدايا)\n\n" +
          "مثال: **ما هي متطلبات الشفافية في أنظمة الذكاء الاصطناعي؟**",
      },
    ]);
    const [input, setInput] = useState("");
    const [isConnecting, setIsConnecting] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [streamBuffer, setStreamBuffer] = useState("");
    const [lastError, setLastError] = useState("");

    const wsRef = useRef(null);
    const nextIdRef = useRef(1);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const streamBufferRef = useRef("");

    useEffect(() => {
      connectWebSocket();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
      if (messagesEndRef.current) {
        const behavior = streamBuffer ? "auto" : "smooth";
        messagesEndRef.current.scrollIntoView({ behavior });
      }
    }, [messages, streamBuffer]);

    useEffect(() => {
      streamBufferRef.current = streamBuffer;
    }, [streamBuffer]);

    function connectWebSocket() {
      setIsConnecting(true);
      setLastError("");
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => setIsConnecting(false);

      ws.onclose = () => {
        setIsConnecting(true);
        setTimeout(() => connectWebSocket(), 1500);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error", err);
        setLastError("WebSocket error. Check backend is running.");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "chunk") {
            setStreamBuffer((prev) => prev + data.text);
          } else if (data.type === "done") {
            const finalText = (streamBufferRef.current || "").trim();
            if (finalText) {
              const id = nextIdRef.current++;
              setMessages((prev) => [
                ...prev,
                { id, role: "assistant", text: streamBufferRef.current },
              ]);
              setStreamBuffer("");
            }
            setIsSending(false);
          }
        } catch (e) {
          console.error("Bad message from server:", event.data, e);
          setLastError("Bad server message. Check backend logs.");
        }
      };
    }

    function handleNewChat() {
      setMessages([
        {
          id: 0,
          role: "assistant",
          text:
            "مرحباً! أنا مساعد تحليلات الأعمال والامتثال لسدايا.\n\n" +
            "- اسألني عن بيانات المبيعات والأرباح\n" +
            "- أو اسألني عن مبادئ أخلاقيات الذكاء الاصطناعي (سدايا)\n\n" +
            "مثال: **ما هي متطلبات الشفافية في أنظمة الذكاء الاصطناعي؟**",
        },
      ]);
      setStreamBuffer("");
    }

    function handleSubmit(e) {
      e.preventDefault();
      const text = input.trim();
      if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      const id = nextIdRef.current++;
      setMessages((prev) => [...prev, { id, role: "user", text }]);
      setInput("");
      setIsSending(true);
      setStreamBuffer("");
      wsRef.current.send(text);
    }

    function autosize() {
      const el = textareaRef.current;
      if (!el) return;
      el.style.height = "0px";
      el.style.height = Math.min(el.scrollHeight, 140) + "px";
    }

    useEffect(() => {
      autosize();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [input]);

    function onKeyDown(e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    }

    return React.createElement(ChatLayout, {
      sidebar: React.createElement(Sidebar, {
        onSuggestionClick: (s) => setInput(s),
        lastError,
        isConnecting,
        isSending,
        onNewChat: handleNewChat,
      }),
      messages: React.createElement(MessageList, {
        messages,
        streamBuffer,
        isSending,
        messagesEndRef,
      }),
      input: React.createElement(ChatInput, {
        input,
        onChange: (e) => setInput(e.target.value),
        onSubmit: handleSubmit,
        onKeyDown,
        textareaRef,
        isConnecting,
        isSending,
      }),
    });
  }

  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(React.createElement(ChatApp));
})();