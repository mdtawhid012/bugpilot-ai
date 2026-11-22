export function ErrorState({ title, message, retry }: { title: string; message: string; retry?: () => void }) {
  return (
    <div className="error-state" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
      {retry ? <button className="button secondary" onClick={retry}>Try again</button> : null}
    </div>
  );
}
