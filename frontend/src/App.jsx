import { useState } from 'react';
import axios from 'axios';
import { Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

function App() {
  // Hardcode the rubric_id you just tested successfully in the backend
  // Replace this with your actual working UUID!
  const TEST_RUBRIC_ID = '3a5b091d-001e-43ea-8228-8b51d7fdfdfc';

  const [reviewText, setReviewText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmitReview = async () => {
    if (!reviewText.trim()) return;

    setIsLoading(true);
    setError('');
    setValidationResult(null);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/validate-review', {
        rubric_id: TEST_RUBRIC_ID,
        review_text: reviewText,
      });

      if (response.data.status === 'success') {
        setValidationResult(response.data.data);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to connect to the AI Interceptor.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-header">
        <div>
          <div className="app-logo">PeerGuard</div>
          <h1 className="app-title">Peer Review Assistant</h1>
          <p className="app-subtitle">
            Paste your feedback, and let the AI check tone, coverage, and alignment with the rubric.
          </p>
        </div>
        <div className="app-badge">Student Mode</div>
      </div>

      <div className="app-grid">
        {/* Left: context */}
        <section className="card card-context">
          <div className="card-label">
            <AlertTriangle size={16} />
            <span>Assignment context</span>
          </div>

          <h2 className="card-title">React Context API & Debounce Hook</h2>
          <p className="card-text">
            You are reviewing a peer&apos;s implementation of a shared state store using React Context and a custom
            300ms debounce hook for search.
          </p>
          <p className="card-text">
            Focus on clarity of explanation, correctness of technical claims, and whether the feedback is constructive
            and actionable.
          </p>

          <div className="card-footer">
            <span className="muted-label">Active rubric</span>
            <code className="pill-code">{TEST_RUBRIC_ID.substring(0, 8)}…</code>
          </div>
        </section>

        {/* Right: interaction */}
        <section className="card card-interaction">
          <label className="field-label" htmlFor="review-text">
            Your feedback to your peer
          </label>
          <textarea
            id="review-text"
            className="textarea"
            placeholder="Be specific about what works well, what is confusing, and how the code could be improved…"
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
          />

          <button
            className="button-primary"
            onClick={handleSubmitReview}
            disabled={isLoading || !reviewText.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 className="spin" size={18} />
                <span>AI is analyzing your feedback…</span>
              </>
            ) : (
              'Run AI check'
            )}
          </button>

          {error && <div className="alert alert-error">{error}</div>}

          {validationResult && (
            <div className={`alert ${validationResult.is_valid ? 'alert-success' : 'alert-warning'}`}>
              <div className="alert-icon">
                {validationResult.is_valid ? (
                  <CheckCircle size={22} />
                ) : (
                  <XCircle size={22} />
                )}
              </div>
              <div className="alert-body">
                <h3 className="alert-title">
                  {validationResult.is_valid ? 'Submission accepted' : 'Revision suggested'}
                </h3>
                <p className="alert-text">{validationResult.feedback_to_reviewer}</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;