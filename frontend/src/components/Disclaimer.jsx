export default function Disclaimer({ children }) {
  return (
    <p className="text-xs text-slate2 border-l-2 border-rule pl-3">
      {children ||
        "Scores show semantic similarity and skill overlap between a resume and a job description. They are not a prediction of hiring probability or an ATS ranking. Please review extracted details for errors."}
    </p>
  );
}
