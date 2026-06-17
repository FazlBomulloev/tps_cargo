import { Component, ErrorInfo, ReactNode } from "react";
import { Button, Result } from "antd";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error("ErrorBoundary caught:", error, info);
    }
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="500"
          title="Что-то пошло не так"
          subTitle={
            import.meta.env.DEV && this.state.error
              ? this.state.error.message
              : "Перезагрузите страницу или вернитесь позже"
          }
          extra={
            <Button type="primary" onClick={this.handleReload}>
              Перезагрузить
            </Button>
          }
        />
      );
    }
    return this.props.children;
  }
}
