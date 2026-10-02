import { useEffect, useState } from 'react';

const API = 'http://127.0.0.1:8765';

export type VoiceProfile = {
  id: string;
  name: string;
  language: string;
  isClone: boolean;
  isBuiltin: boolean;
  description?: string;
  referenceAudio?: string | null;
  referenceAudioSha256?: string | null;
  referenceText?: string;
  consentConfirmed: boolean;
  consentTimestamp?: string | null;
  consentStatement?: string | null;
  createdAt?: string;
};

export type AuditEvent = {
  id: string;
  event: string;
  timestamp: string;
  voice_id?: string;
  voice_name?: string;
  reference_audio?: string | null;
  reference_audio_sha256?: string | null;
  reference_text?: string;
  statement?: string;
  output_audio?: string;
  output_audio_sha256?: string | null;
  consent_confirmed?: boolean;
  cached?: boolean;
  model_revision?: string;
};

async function json(path: string, init?: RequestInit) {
  const r = await fetch(API + path, init);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || JSON.stringify(data));
  return data;
}

export default function VoiceManager() {
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showAudit, setShowAudit] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Form states
  const [voiceId, setVoiceId] = useState('');
  const [name, setName] = useState('');
  const [language, setLanguage] = useState('vi');
  const [isClone, setIsClone] = useState(false);
  const [refAudio, setRefAudio] = useState('');
  const [refText, setRefText] = useState('');
  const [consentChecked, setConsentChecked] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadVoices = async () => {
    try {
      setVoices(await json('/voices'));
    } catch (e) {
      setError(String(e));
    }
  };

  const loadAudit = async () => {
    try {
      setAuditLogs(await json('/audit/voice-clones?limit=30'));
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => {
    loadVoices();
  }, []);

  const openCreateModal = () => {
    setVoiceId('');
    setName('');
    setLanguage('vi');
    setIsClone(false);
    setRefAudio('');
    setRefText('');
    setConsentChecked(false);
    setError('');
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!voiceId.trim()) {
      setError('Vui lòng nhập Voice ID');
      return;
    }
    if (isClone) {
      if (!refAudio.trim()) {
        setError('Voice clone yêu cầu đường dẫn file reference audio (.wav)');
        return;
      }
      if (!consentChecked) {
        setError('Bắt buộc đọc và xác nhận cam kết bản quyền/pháp lý trước khi tạo voice clone');
        return;
      }
    }

    setSaving(true);
    setError('');
    try {
      await json('/voices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: voiceId.trim().toLowerCase(),
          name: name.trim() || voiceId.trim(),
          language,
          isClone,
          referenceAudio: isClone ? refAudio.trim() : null,
          referenceText: isClone ? refText.trim() : '',
          consentConfirmed: isClone ? consentChecked : true,
          consentStatement: isClone
            ? 'Tôi cam kết rằng tôi sở hữu hoặc đã được chủ sở hữu ủy quyền hợp pháp bằng văn bản để sử dụng mẫu giọng nói này cho mục đích tổng hợp giọng nói AI (Voice Clone). Tôi cam kết không sử dụng giọng nói này để mạo danh, lừa đảo, tạo tin giả hoặc vi phạm pháp luật và quyền riêng tư của cá nhân khác.'
            : '',
        }),
      });
      setNotice(`Đã lưu Voice Profile ${voiceId} thành công.`);
      setShowModal(false);
      await loadVoices();
      if (showAudit) await loadAudit();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Xóa voice profile ${id}?`)) return;
    try {
      await json(`/voices/${id}`, { method: 'DELETE' });
      setNotice(`Đã xóa voice profile ${id}`);
      await loadVoices();
    } catch (e) {
      setError(String(e));
    }
  };

  const toggleAudit = async () => {
    if (!showAudit) {
      await loadAudit();
    }
    setShowAudit(!showAudit);
  };

  return (
    <section className="voice-manager">
      <div className="row">
        <div>
          <h2>Voice Profiles & Consent Guard</h2>
          <small>Quản lý giọng đọc TTS chuẩn và Zero-shot Voice Clone có xác nhận bản quyền và audit metadata.</small>
        </div>
        <div className="buttons">
          <button onClick={toggleAudit}>{showAudit ? 'Đóng Audit Log' : 'Xem Audit Log'}</button>
          <button className="list add" onClick={openCreateModal}>+ Tạo Voice Profile</button>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="alert">{error}</div>}

      <div className="cards" style={{ marginTop: '16px' }}>
        {voices.map((v) => (
          <div className="model voice-card" key={v.id}>
            <div className="row">
              <b>{v.name}</b>
              <span className={`tag ${v.isClone ? 'clone' : 'installed'}`}>
                {v.isBuiltin ? 'Mặc định' : v.isClone ? 'Voice Clone' : 'Custom TTS'}
              </span>
            </div>
            <small>ID: <code>{v.id}</code> · Ngôn ngữ: <b>{v.language.toUpperCase()}</b></small>
            {v.description && <small>{v.description}</small>}
            {v.isClone && (
              <>
                <small title={v.referenceAudio || ''}>
                  File mẫu: <code>{v.referenceAudio ? v.referenceAudio.split(/[/\\]/).pop() : 'N/A'}</code>
                </small>
                {v.referenceAudioSha256 && (
                  <small title={v.referenceAudioSha256}>
                    SHA-256: <code>{v.referenceAudioSha256.slice(0, 14)}...</code>
                  </small>
                )}
                <div className="consent-badge">
                  ✓ Quyền sử dụng đã xác nhận ({v.consentTimestamp ? new Date(v.consentTimestamp).toLocaleDateString() : 'Đã duyệt'})
                </div>
              </>
            )}
            <div className="buttons">
              {!v.isBuiltin && (
                <button className="danger" onClick={() => handleDelete(v.id)}>Xóa</button>
              )}
            </div>
          </div>
        ))}
      </div>

      {showAudit && (
        <div className="audit-section" style={{ marginTop: '20px' }}>
          <div className="row">
            <h3>Nhật ký Audit Metadata (Voice Clones & Synthesis)</h3>
            <button onClick={loadAudit}>Làm mới</button>
          </div>
          {auditLogs.length === 0 ? (
            <p>Chưa có bản ghi audit nào.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Thời gian (UTC)</th>
                    <th>Sự kiện</th>
                    <th>Voice / Ref SHA-256</th>
                    <th>Consent</th>
                    <th>Output File / Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td><small>{new Date(log.timestamp).toLocaleString()}</small></td>
                      <td>
                        <span className={`tag ${log.event.includes('consent') ? 'installed' : ''}`}>
                          {log.event}
                        </span>
                      </td>
                      <td>
                        <small>
                          {log.voice_id || (log.reference_audio_sha256 ? `${log.reference_audio_sha256.slice(0, 10)}...` : 'TTS chuẩn')}
                        </small>
                      </td>
                      <td>
                        <span className={log.consent_confirmed ? 'ok-text' : ''}>
                          {log.consent_confirmed ? '✓ Verified' : 'N/A'}
                        </span>
                      </td>
                      <td>
                        <small title={log.output_audio || ''}>
                          {log.output_audio ? log.output_audio.split(/[/\\]/).pop() : '-'}
                          {log.output_audio_sha256 ? ` (${log.output_audio_sha256.slice(0, 8)})` : ''}
                        </small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="row">
              <h3>Tạo Voice Profile Mới</h3>
              <button onClick={() => setShowModal(false)}>✕</button>
            </div>

            <div className="form-group">
              <label>Voice ID (chữ thường, số, gạch ngang):</label>
              <input
                type="text"
                placeholder="vi-du: giong-bac-nam"
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Tên hiển thị:</label>
              <input
                type="text"
                placeholder="Giọng Đọc Hà Nội Nam"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Ngôn ngữ:</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="vi">Tiếng Việt (vi)</option>
                <option value="en">English (en)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={isClone}
                  onChange={(e) => setIsClone(e.target.checked)}
                />
                <b>Kích hoạt chế độ Nhân bản giọng nói (Zero-shot Voice Clone)</b>
              </label>
            </div>

            {isClone && (
              <div className="clone-fields">
                <div className="form-group">
                  <label>Đường dẫn file mẫu âm thanh (WAV/FLAC trên máy):</label>
                  <input
                    type="text"
                    placeholder="C:\audio\mau-giong.wav"
                    value={refAudio}
                    onChange={(e) => setRefAudio(e.target.value)}
                  />
                  <small>Khuyến nghị file WAV 48kHz hoặc 44.1kHz sạch, độ dài 5-15 giây.</small>
                </div>

                <div className="form-group">
                  <label>Văn bản tương ứng với file mẫu (Reference text):</label>
                  <textarea
                    rows={2}
                    placeholder="Nhập nội dung được nói trong file mẫu để tăng độ chuẩn xác..."
                    value={refText}
                    onChange={(e) => setRefText(e.target.value)}
                  />
                </div>

                <div className="consent-box">
                  <div className="legal-warning">
                    ⚠️ <b>CẢNH BÁO ĐẠO ĐỨC & PHÁP LÝ NHÂN BẢN GIỌNG NÓI</b>
                  </div>
                  <p className="consent-text">
                    "Tôi cam kết rằng tôi sở hữu hoặc đã được chủ sở hữu ủy quyền hợp pháp bằng văn bản
                    để sử dụng mẫu giọng nói này cho mục đích tổng hợp giọng nói AI (Voice Clone).
                    Tôi cam kết không sử dụng giọng nói này để mạo danh, lừa đảo, tạo tin giả hoặc
                    vi phạm pháp luật và quyền riêng tư của cá nhân khác."
                  </p>
                  <label className="checkbox-row consent-check">
                    <input
                      type="checkbox"
                      checked={consentChecked}
                      onChange={(e) => setConsentChecked(e.target.checked)}
                    />
                    <span>
                      <b>Tôi xác nhận đã đọc, hiểu rõ và chịu hoàn toàn trách nhiệm pháp lý.</b>
                    </span>
                  </label>
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button onClick={() => setShowModal(false)}>Hủy bỏ</button>
              <button
                disabled={saving || (isClone && !consentChecked)}
                className="list add"
                onClick={handleSave}
              >
                {saving ? 'Đang lưu...' : 'Xác nhận & Lưu Voice Profile'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
