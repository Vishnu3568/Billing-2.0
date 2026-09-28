import React, { useState, useEffect, useRef } from 'react';
import { dutySlipService, companyService, extractionService } from '../api/client';
import { 
  FileText, 
  Plus, 
  Search, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  X, 
  Upload, 
  Eye, 
  Edit3, 
  Trash2, 
  Building2, 
  ExternalLink,
  Sparkles,
  AlertTriangle,
  FileSearch,
  CheckCircle,
  HelpCircle,
  Scan,
  ShieldCheck,
  History,
  Check,
  ArrowRight,
  FileDown
} from 'lucide-react';


export function DutySlips() {
  const [dutySlips, setDutySlips] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Filters
  const [selectedCompanyFilter, setSelectedCompanyFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Upload Modal State
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadCompanyId, setUploadCompanyId] = useState('');
  const [uploadDutySlipNo, setUploadDutySlipNo] = useState('');
  const [uploadNotes, setUploadNotes] = useState('');
  const [frontFile, setFrontFile] = useState(null);
  const [backFile, setBackFile] = useState(null);
  const [frontPreview, setFrontPreview] = useState(null);
  const [backPreview, setBackPreview] = useState(null);
  const [uploadFormError, setUploadFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // View Scans Modal State
  const [viewModalSlip, setViewModalSlip] = useState(null);
  const [activeScanTab, setActiveScanTab] = useState('front'); // 'front' | 'back'

  // Human Review & Editing Modal State (Step 6)
  const [reviewModalState, setReviewModalState] = useState(null); // { slip, extraction }
  const [reviewScanTab, setReviewScanTab] = useState('front');
  const [reviewFormValues, setReviewFormValues] = useState({});
  const [reviewerName, setReviewerName] = useState('Human Reviewer');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewVerifying, setReviewVerifying] = useState(false);
  const [reviewError, setReviewError] = useState(null);
  const [reviewSuccess, setReviewSuccess] = useState(null);
  const [activeReviewSection, setActiveReviewSection] = useState('fields'); // 'fields' | 'audit'

  const [runningOcrSlipId, setRunningOcrSlipId] = useState(null);

  // Edit Metadata Modal State
  const [editModalSlip, setEditModalSlip] = useState(null);
  const [editDutySlipNo, setEditDutySlipNo] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [editFormError, setEditFormError] = useState(null);
  const [editSubmitting, setEditSubmitting] = useState(false);

  // Delete Confirmation Modal State
  const [deleteModalSlip, setDeleteModalSlip] = useState(null);
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  // Word Document Generation & PDF Preview State (Step 7)
  const [generatingWordSlipId, setGeneratingWordSlipId] = useState(null);
  const [pdfViewerModal, setPdfViewerModal] = useState(null); // { companyId, companyName }

  const frontInputRef = useRef(null);
  const backInputRef = useRef(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [comps, slips] = await Promise.all([
        companyService.getCompanies(true),
        dutySlipService.getDutySlips({
          companyId: selectedCompanyFilter || undefined,
          search: searchQuery || undefined,
        }),
      ]);
      setCompanies(comps);
      setDutySlips(slips);
    } catch (err) {
      setError(err.message || 'Failed to load duty slips.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedCompanyFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  // Upload Handlers
  const openUploadModal = () => {
    setUploadCompanyId(companies.length > 0 ? companies[0].id : '');
    setUploadDutySlipNo('');
    setUploadNotes('');
    setFrontFile(null);
    setBackFile(null);
    setFrontPreview(null);
    setBackPreview(null);
    setUploadFormError(null);
    setIsUploadModalOpen(true);
  };

  const closeUploadModal = () => {
    setIsUploadModalOpen(false);
    if (frontPreview) URL.revokeObjectURL(frontPreview);
    if (backPreview) URL.revokeObjectURL(backPreview);
    setFrontFile(null);
    setBackFile(null);
    setFrontPreview(null);
    setBackPreview(null);
  };

  const handleFrontFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFrontFile(file);
      if (file.type.startsWith('image/')) {
        setFrontPreview(URL.createObjectURL(file));
      } else {
        setFrontPreview(null);
      }
    }
  };

  const handleBackFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setBackFile(file);
      if (file.type.startsWith('image/')) {
        setBackPreview(URL.createObjectURL(file));
      } else {
        setBackPreview(null);
      }
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadCompanyId) {
      setUploadFormError('Please select a company.');
      return;
    }
    if (!uploadDutySlipNo.trim()) {
      setUploadFormError('Duty slip number is required (e.g. 1, 2, 3).');
      return;
    }
    if (!frontFile) {
      setUploadFormError('Front scan is required.');
      return;
    }

    setSubmitting(true);
    setUploadFormError(null);

    const formData = new FormData();
    formData.append('company_id', uploadCompanyId);
    formData.append('duty_slip_no', uploadDutySlipNo.trim());
    if (uploadNotes.trim()) formData.append('notes', uploadNotes.trim());
    formData.append('front_file', frontFile);
    if (backFile) {
      formData.append('back_file', backFile);
    }

    try {
      const created = await dutySlipService.createDutySlip(formData);
      setSuccessMessage(`Duty Slip "${created.duty_slip_no}" uploaded successfully.`);
      closeUploadModal();
      await fetchData();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setUploadFormError(err.message || 'Failed to upload duty slip.');
    } finally {
      setSubmitting(false);
    }
  };

  // OCR Extraction Handler
  const handleRunOcr = async (slip) => {
    setRunningOcrSlipId(slip.id);
    setError(null);
    try {
      const result = await extractionService.extract(slip.id);
      setSuccessMessage(`OCR extraction completed for Duty Slip #${slip.duty_slip_no}.`);
      await fetchData();
      openReviewModal(slip, result);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'OCR extraction failed.');
    } finally {
      setRunningOcrSlipId(null);
    }
  };

  // Review & Edit Modal Handlers (Step 6)
  const openReviewModal = async (slip, preloadedExtraction = null) => {
    setReviewLoading(true);
    setReviewError(null);
    setReviewSuccess(null);
    setReviewScanTab('front');
    setActiveReviewSection('fields');
    try {
      const extraction = preloadedExtraction || await extractionService.getExtraction(slip.id);
      
      // Initialize form values from extraction fields
      const initialValues = {};
      if (extraction && extraction.fields) {
        Object.entries(extraction.fields).forEach(([fieldName, fData]) => {
          initialValues[fieldName] = fData.value !== null && fData.value !== undefined ? String(fData.value) : '';
        });
      }
      setReviewFormValues(initialValues);
      setReviewModalState({ slip, extraction });
    } catch (err) {
      setError(err.message || 'Failed to load extraction for review.');
    } finally {
      setReviewLoading(false);
    }
  };

  const closeReviewModal = () => {
    setReviewModalState(null);
    setReviewFormValues({});
    setReviewError(null);
    setReviewSuccess(null);
  };

  const handleReviewFieldChange = (fieldName, val) => {
    setReviewFormValues(prev => ({
      ...prev,
      [fieldName]: val
    }));
  };

  const handleSaveCorrections = async () => {
    if (!reviewModalState) return;
    setReviewSaving(true);
    setReviewError(null);
    setReviewSuccess(null);

    // Format payload converting strings to null if empty
    const payloadFields = {};
    Object.entries(reviewFormValues).forEach(([k, v]) => {
      payloadFields[k] = v.trim() === '' ? null : v.trim();
    });

    try {
      const updatedExtraction = await extractionService.updateExtraction(
        reviewModalState.slip.id,
        payloadFields,
        reviewerName || 'reviewer',
        reviewNotes || null
      );
      setReviewModalState(prev => ({ ...prev, extraction: updatedExtraction }));
      setReviewSuccess('Corrections saved and consistency re-validated successfully.');
      await fetchData();
      setTimeout(() => setReviewSuccess(null), 4000);
    } catch (err) {
      setReviewError(err.message || 'Failed to save corrections.');
    } finally {
      setReviewSaving(false);
    }
  };

  const handleVerifyExtraction = async () => {
    if (!reviewModalState) return;
    setReviewVerifying(true);
    setReviewError(null);
    setReviewSuccess(null);

    try {
      // First save any unsaved field changes
      const payloadFields = {};
      Object.entries(reviewFormValues).forEach(([k, v]) => {
        payloadFields[k] = v.trim() === '' ? null : v.trim();
      });

      const updated = await extractionService.updateExtraction(
        reviewModalState.slip.id,
        payloadFields,
        reviewerName || 'reviewer',
        reviewNotes || null
      );

      // Now call verify
      const verified = await extractionService.verifyExtraction(
        reviewModalState.slip.id,
        reviewerName || 'reviewer',
        reviewNotes || null
      );

      setReviewModalState(prev => ({ ...prev, extraction: verified }));
      setReviewSuccess('Duty slip extraction has been officially APPROVED & VERIFIED!');
      setSuccessMessage(`Duty Slip #${reviewModalState.slip.duty_slip_no} verified successfully.`);
      await fetchData();
    } catch (err) {
      setReviewError(err.message || 'Verification failed. Please resolve all validation conflicts first.');
    } finally {
      setReviewVerifying(false);
    }
  };

  // Word Document Generation Handler (Step 7: Company Master Document)
  const handleGenerateWordBill = async (slip) => {
    if (!slip) return;
    setGeneratingWordSlipId(slip.id);
    setError(null);
    setSuccessMessage(null);
    try {
      const res = await dutySlipService.generateWordBill(slip.id);
      setSuccessMessage(`Bill (${res.bill_no}) generated successfully for ${res.company_name || 'company'}. Master Document updated (Total bills: ${res.total_bills_in_doc}).`);
      await fetchData();
      // Automatically open the PDF Preview modal for the company master document
      setPdfViewerModal({
        companyId: slip.company_id,
        companyName: slip.company_name || 'Company',
      });
      setTimeout(() => setSuccessMessage(null), 6000);
    } catch (err) {
      setError(err.message || 'Failed to generate Word Bill.');
    } finally {
      setGeneratingWordSlipId(null);
    }
  };

  // Edit Metadata Handlers
  const openEditModal = (slip) => {
    setEditModalSlip(slip);
    setEditDutySlipNo(slip.duty_slip_no);
    setEditNotes(slip.notes || '');
    setEditFormError(null);
  };

  const closeEditModal = () => {
    setEditModalSlip(null);
    setEditFormError(null);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editDutySlipNo.trim()) {
      setEditFormError('Duty slip number cannot be empty.');
      return;
    }

    setEditSubmitting(true);
    setEditFormError(null);
    try {
      const updated = await dutySlipService.updateDutySlip(editModalSlip.id, {
        duty_slip_no: editDutySlipNo.trim(),
        notes: editNotes.trim() || null,
      });
      setSuccessMessage(`Duty Slip "${updated.duty_slip_no}" updated successfully.`);
      closeEditModal();
      await fetchData();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setEditFormError(err.message || 'Failed to update metadata.');
    } finally {
      setEditSubmitting(false);
    }
  };

  // Delete Handlers
  const openDeleteModal = (slip) => {
    setDeleteModalSlip(slip);
    setDeleteError(null);
  };

  const closeDeleteModal = () => {
    setDeleteModalSlip(null);
    setDeleteError(null);
  };

  const handleConfirmDelete = async () => {
    if (!deleteModalSlip) return;
    setDeleteSubmitting(true);
    setDeleteError(null);
    try {
      await dutySlipService.deleteDutySlip(deleteModalSlip.id);
      setSuccessMessage(`Duty slip #${deleteModalSlip.duty_slip_no} deleted successfully.`);
      closeDeleteModal();
      await fetchData();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete duty slip.');
    } finally {
      setDeleteSubmitting(false);
    }
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'verified':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Verified
          </span>
        );
      case 'extracted':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
            <Sparkles className="w-3 h-3 text-sky-500" />
            Extracted
          </span>
        );
      case 'needs_review':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-500" />
            Needs Review
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
            <RefreshCw className="w-3 h-3 text-sky-500 animate-spin" />
            Processing
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-500" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <Upload className="w-3 h-3 text-slate-400" />
            Uploaded
          </span>
        );
    }
  };

  // Helper for rendering editable input in Review modal
  const renderFieldEditor = (fieldName, label, placeholder = '', hint = '') => {
    if (!reviewModalState || !reviewModalState.extraction) return null;
    const fData = reviewModalState.extraction.fields[fieldName] || {};
    const val = reviewFormValues[fieldName] ?? '';
    const isEdited = fData.edited;
    const hasOriginal = fData.original_value !== null && fData.original_value !== undefined;
    const confidencePct = (fData.confidence * 100).toFixed(0);

    return (
      <div className={`p-2.5 rounded-lg border transition-colors ${
        fData.needs_review 
          ? 'bg-amber-50/50 border-amber-300' 
          : isEdited 
            ? 'bg-indigo-50/40 border-indigo-200' 
            : 'bg-white border-slate-200'
      }`}>
        <div className="flex items-center justify-between gap-2 mb-1">
          <label className="text-[11px] font-semibold text-slate-700 capitalize flex items-center gap-1">
            {label}
            {hint && <span className="text-[10px] font-normal text-slate-400">({hint})</span>}
          </label>
          <div className="flex items-center gap-1.5">
            {isEdited ? (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
                Edited
              </span>
            ) : fData.needs_review ? (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                Review
              </span>
            ) : (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700">
                {confidencePct}%
              </span>
            )}
          </div>
        </div>

        <input
          type="text"
          value={val}
          placeholder={placeholder || `Enter ${label}`}
          onChange={(e) => handleReviewFieldChange(fieldName, e.target.value)}
          className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono text-slate-900 bg-white"
        />

        {/* Show original OCR value if edited or flagged */}
        {isEdited && hasOriginal && (
          <div className="text-[10px] text-indigo-700 mt-1 flex items-center justify-between">
            <span>OCR Original: <span className="font-mono font-medium">{String(fData.original_value)}</span></span>
            {fData.edited_at && (
              <span className="text-slate-400">
                {new Date(fData.edited_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        )}

        {fData.review_reason && !isEdited && (
          <div className="text-[10px] text-amber-700 mt-1 font-mono">
            {fData.review_reason}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-sky-600" />
            Duty Slip Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Store scans, run OCR extraction, and perform Human Review & Verification before billing.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={openUploadModal}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Upload Duty Slip
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between gap-3 text-emerald-800 animate-in fade-in">
          <div className="flex items-center gap-2 text-sm font-medium">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between gap-3 text-rose-800">
          <div className="flex items-center gap-2 text-sm font-medium">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
        {/* Company filter */}
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-500 mb-1">Filter by Company</label>
          <select
            value={selectedCompanyFilter}
            onChange={(e) => setSelectedCompanyFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500 text-slate-800"
          >
            <option value="">All Companies</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {!c.is_active ? '(Inactive)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Search input */}
        <div className="flex-1">
          <label className="block text-xs font-medium text-slate-500 mb-1">Search Duty Slip #</label>
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="e.g. 1, 2, 47"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500 text-slate-800"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading duty slips...</p>
        </div>
      ) : dutySlips.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">No duty slips found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
            {companies.length === 0 
              ? "Create a company first before uploading duty slips."
              : "Upload duty slip front and back scans to manage records and run OCR extraction."}
          </p>
          <div className="mt-6">
            <button
              onClick={openUploadModal}
              disabled={companies.length === 0}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-colors disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              Upload First Duty Slip
            </button>
          </div>
        </div>
      ) : (
        /* Duty Slips Table */
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-3.5">Duty Slip #</th>
                <th className="px-6 py-3.5">Company</th>
                <th className="px-6 py-3.5">Attached Scans</th>
                <th className="px-6 py-3.5">Verification Status</th>
                <th className="px-6 py-3.5">Upload Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {dutySlips.map((slip) => (
                <tr key={slip.id} className="hover:bg-slate-50/75 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-900 text-base">#{slip.duty_slip_no}</div>
                    {slip.notes && <div className="text-xs text-slate-400 mt-0.5">{slip.notes}</div>}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 text-slate-700 font-medium">
                      <Building2 className="w-4 h-4 text-slate-400" />
                      {slip.company_name || 'Unknown Company'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setViewModalSlip(slip);
                          setActiveScanTab('front');
                        }}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs transition-colors"
                        title="View Front Scan"
                      >
                        <Eye className="w-3 h-3 text-sky-600" />
                        Front
                      </button>
                      {(slip.has_back_scan || slip.back_scan) ? (
                        <button
                          onClick={() => {
                            setViewModalSlip(slip);
                            setActiveScanTab('back');
                          }}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs transition-colors"
                          title="View Back Scan"
                        >
                          <Eye className="w-3 h-3 text-indigo-600" />
                          Back
                        </button>
                      ) : (
                        <span className="text-[10px] text-slate-400 italic px-1.5 py-0.5 bg-slate-50 border border-slate-200 rounded">
                          Front Only
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {renderStatusBadge(slip.status)}
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-xs">
                    {new Date(slip.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {/* Primary Workflow Button: Run OCR or Review */}
                    {slip.status === 'uploaded' || slip.status === 'failed' ? (
                      <button
                        onClick={() => handleRunOcr(slip)}
                        disabled={runningOcrSlipId === slip.id}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-colors disabled:opacity-50"
                        title="Run OCR Extraction"
                      >
                        <Sparkles className={`w-3.5 h-3.5 ${runningOcrSlipId === slip.id ? 'animate-spin' : ''}`} />
                        {runningOcrSlipId === slip.id ? 'Extracting...' : 'Run OCR'}
                      </button>
                    ) : (
                      <button
                        onClick={() => openReviewModal(slip)}
                        className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors shadow-sm ${
                          slip.status === 'verified'
                            ? 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200'
                            : 'bg-amber-600 text-white hover:bg-amber-700'
                        }`}
                        title="Human Review & Editing"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        {slip.status === 'verified' ? 'Inspect Verified' : 'Review & Verify'}
                      </button>
                    )}

                    {/* Step 7: Company Master Document Actions */}
                    {slip.status === 'verified' && (
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => handleGenerateWordBill(slip)}
                          disabled={generatingWordSlipId === slip.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-semibold shadow-sm transition-colors disabled:opacity-50 bg-indigo-600 hover:bg-indigo-700 text-white"
                          title="Generate/Update Bill in Company Master Document"
                        >
                          <FileDown className={`w-3.5 h-3.5 ${generatingWordSlipId === slip.id ? 'animate-spin' : ''}`} />
                          {generatingWordSlipId === slip.id ? 'Generating...' : slip.has_word_bill ? 'Regenerate' : 'Generate Bill'}
                        </button>
                        {slip.has_word_bill && (
                          <button
                            onClick={() => setPdfViewerModal({ companyId: slip.company_id, companyName: slip.company_name })}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold shadow-sm transition-colors bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
                            title="View Company Master Document PDF Preview in Browser"
                          >
                            <Eye className="w-3.5 h-3.5 text-blue-600" />
                            View Doc
                          </button>
                        )}
                      </div>
                    )}

                    <button
                      onClick={() => {
                        setViewModalSlip(slip);
                        setActiveScanTab('front');
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                      title="View Scans"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => openEditModal(slip)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                      title="Edit Metadata"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => openDeleteModal(slip)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
                      title="Delete Duty Slip"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* STEP 6: HUMAN REVIEW & EDITING MODAL */}
      {reviewModalState && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-950/70 backdrop-blur-sm overflow-y-auto">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-6xl w-full overflow-hidden my-4 animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[95vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-sky-500/20 text-sky-400 rounded-lg border border-sky-500/30">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold tracking-tight">
                      Duty Slip #{reviewModalState.slip.duty_slip_no} — Human Review & Verification
                    </h3>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                      reviewModalState.extraction.status === 'verified'
                        ? 'bg-emerald-500 text-slate-950'
                        : reviewModalState.extraction.status === 'needs_review'
                          ? 'bg-amber-400 text-slate-950'
                          : 'bg-sky-400 text-slate-950'
                    }`}>
                      {reviewModalState.extraction.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Company: <span className="text-slate-200 font-medium">{reviewModalState.slip.company_name}</span> • Provider: <span className="text-slate-200 font-mono">{reviewModalState.extraction.provider_used}</span> • Confidence: <span className="text-slate-200 font-semibold">{(reviewModalState.extraction.overall_confidence * 100).toFixed(0)}%</span>
                  </p>
                </div>
              </div>
              <button onClick={closeReviewModal} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Error / Success Alerts */}
            {reviewError && (
              <div className="mx-6 mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-rose-800 text-xs">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                  <span className="font-medium">{reviewError}</span>
                </div>
                <button onClick={() => setReviewError(null)} className="text-rose-500 hover:text-rose-700">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {reviewSuccess && (
              <div className="mx-6 mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-800 text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span className="font-semibold">{reviewSuccess}</span>
                </div>
                <button onClick={() => setReviewSuccess(null)} className="text-emerald-500 hover:text-emerald-700">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Split Screen Body */}
            <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-200 min-h-[500px]">
              
              {/* LEFT PANEL: Original Scans Viewer (5 cols) */}
              <div className="lg:col-span-5 flex flex-col bg-slate-100 overflow-hidden">
                {/* Scan side tab switcher */}
                <div className="px-4 pt-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div className="flex space-x-1">
                    <button
                      onClick={() => setReviewScanTab('front')}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-t-md border-b-2 transition-colors ${
                        reviewScanTab === 'front'
                          ? 'border-sky-600 text-sky-700 bg-white shadow-sm'
                          : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Front Scan
                    </button>
                    {(reviewModalState.slip.has_back_scan || reviewModalState.slip.back_scan) ? (
                      <button
                        onClick={() => setReviewScanTab('back')}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-t-md border-b-2 transition-colors ${
                          reviewScanTab === 'back'
                            ? 'border-indigo-600 text-indigo-700 bg-white shadow-sm'
                            : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        Back Scan
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-400 italic px-2 py-1 bg-slate-100 rounded">
                        Front Only (No Back)
                      </span>
                    )}
                  </div>

                  {reviewModalState.slip[`${reviewScanTab}_scan`] && (
                    <a
                      href={dutySlipService.getScanUrl(reviewModalState.slip.id, reviewScanTab)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-sky-600 hover:text-sky-800 font-medium pb-1"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Full Image
                    </a>
                  )}
                </div>

                {/* Scan Image Display */}
                <div className="flex-1 p-3 overflow-auto flex items-center justify-center bg-slate-200/60 min-h-[300px]">
                  {reviewModalState.slip[`${reviewScanTab}_scan`] ? (
                    reviewModalState.slip[`${reviewScanTab}_scan`].content_type.startsWith('image/') ? (
                      <img
                        src={dutySlipService.getScanUrl(reviewModalState.slip.id, reviewScanTab)}
                        alt={`${reviewScanTab} scan`}
                        className="max-h-[65vh] w-auto max-w-full object-contain rounded-lg shadow-md border border-slate-300 bg-white"
                      />
                    ) : (
                      <iframe
                        src={dutySlipService.getScanUrl(reviewModalState.slip.id, reviewScanTab)}
                        title={`${reviewScanTab} scan document`}
                        className="w-full h-[65vh] rounded-lg border border-slate-300 bg-white"
                      />
                    )
                  ) : (
                    <div className="text-center p-6 text-slate-400 text-xs">
                      No back scan exists for this single-sided duty slip.
                    </div>
                  )}
                </div>

                {/* Left footer note */}
                <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 text-[10px] text-slate-500 flex items-center justify-between">
                  <span>Source Scans are read-only and preserved permanently.</span>
                </div>
              </div>

              {/* RIGHT PANEL: Editable OCR Fields & Verification (7 cols) */}
              <div className="lg:col-span-7 flex flex-col bg-white overflow-hidden">
                
                {/* Sub-nav tabs: Fields vs Audit Trail */}
                <div className="px-6 pt-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setActiveReviewSection('fields')}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-t-md border-b-2 transition-colors ${
                        activeReviewSection === 'fields'
                          ? 'border-sky-600 text-sky-700 bg-white shadow-sm'
                          : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      Extracted Fields & Edits
                    </button>
                    <button
                      onClick={() => setActiveReviewSection('audit')}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-t-md border-b-2 transition-colors flex items-center gap-1.5 ${
                        activeReviewSection === 'audit'
                          ? 'border-indigo-600 text-indigo-700 bg-white shadow-sm'
                          : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      <History className="w-3.5 h-3.5" />
                      Audit Trail ({reviewModalState.extraction.audit_log?.length || 0})
                    </button>
                  </div>

                  {reviewModalState.extraction.status === 'verified' && (
                    <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1 pb-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified by {reviewModalState.extraction.verified_by || 'reviewer'}
                    </span>
                  )}
                </div>

                {/* Form Body */}
                <div className="flex-1 p-6 overflow-y-auto space-y-5 max-h-[65vh]">
                  
                  {activeReviewSection === 'audit' ? (
                    /* AUDIT TRAIL TAB */
                    <div className="space-y-3">
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-600">
                        Field Modification History
                      </div>
                      {(!reviewModalState.extraction.audit_log || reviewModalState.extraction.audit_log.length === 0) ? (
                        <div className="p-8 text-center bg-slate-50 border border-slate-200 rounded-xl text-slate-400 text-xs">
                          No manual edits recorded yet. All fields currently reflect raw OCR values.
                        </div>
                      ) : (
                        <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                          <table className="min-w-full divide-y divide-slate-200 text-xs">
                            <thead className="bg-slate-50 text-slate-600 font-semibold">
                              <tr>
                                <th className="px-3.5 py-2 text-left">Field</th>
                                <th className="px-3.5 py-2 text-left">Original OCR</th>
                                <th className="px-3.5 py-2 text-left">Corrected Value</th>
                                <th className="px-3.5 py-2 text-left">Reviewer</th>
                                <th className="px-3.5 py-2 text-right">Timestamp</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200 font-mono">
                              {reviewModalState.extraction.audit_log.map((entry, idx) => (
                                <tr key={idx} className="hover:bg-slate-50">
                                  <td className="px-3.5 py-2 font-medium text-slate-800 capitalize font-sans">
                                    {entry.field_name.replace(/_/g, ' ')}
                                  </td>
                                  <td className="px-3.5 py-2 text-rose-700 bg-rose-50/40">
                                    {entry.original_value !== null ? String(entry.original_value) : 'null'}
                                  </td>
                                  <td className="px-3.5 py-2 text-emerald-700 bg-emerald-50/40 font-bold">
                                    {entry.corrected_value !== null ? String(entry.corrected_value) : 'null'}
                                  </td>
                                  <td className="px-3.5 py-2 text-slate-600 font-sans text-[11px]">
                                    {entry.edited_by}
                                  </td>
                                  <td className="px-3.5 py-2 text-right text-slate-400 font-sans text-[11px]">
                                    {new Date(entry.edited_at).toLocaleString()}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ) : (
                    /* FIELDS TAB */
                    <>
                      {/* Duty Slip Number Source Separation Alert */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs">
                        <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                          <div className="text-slate-400 text-[10px] font-medium flex items-center gap-1">
                            <FileText className="w-3 h-3 text-slate-400" />
                            Assigned Duty Slip No. (System ID)
                          </div>
                          <div className="font-bold text-slate-900 font-mono text-base mt-0.5">
                            #{reviewModalState.extraction.stored_duty_slip_no || reviewModalState.slip.duty_slip_no}
                          </div>
                          <div className="text-[10px] text-slate-400">Fixed record metadata</div>
                        </div>

                        <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                          <div className="text-slate-400 text-[10px] font-medium flex items-center gap-1">
                            <Scan className="w-3 h-3 text-sky-500" />
                            Physical Document No. (Editable)
                          </div>
                          <div className="mt-1">
                            <input
                              type="text"
                              placeholder="Blank on document"
                              value={reviewFormValues['duty_slip_no'] ?? ''}
                              onChange={(e) => handleReviewFieldChange('duty_slip_no', e.target.value)}
                              className="w-full px-2 py-1 text-xs rounded border border-slate-300 font-mono text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                            />
                          </div>
                          <div className="text-[10px] text-slate-400 mt-0.5">Enter if printed on physical paper</div>
                        </div>
                      </div>

                      {/* Package Consistency Validation Card */}
                      {reviewModalState.extraction.validation_summary && (
                        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                              Package Consistency (8hr / 80km rules)
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                reviewModalState.extraction.validation_summary.is_km_consistent ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                              }`}>
                                KM: {reviewModalState.extraction.validation_summary.is_km_consistent ? 'PASS' : 'FAIL'}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                reviewModalState.extraction.validation_summary.is_time_consistent ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                              }`}>
                                TIME: {reviewModalState.extraction.validation_summary.is_time_consistent ? 'PASS' : 'FAIL'}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                reviewModalState.extraction.validation_summary.is_math_consistent ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                              }`}>
                                MATH: {reviewModalState.extraction.validation_summary.is_math_consistent ? 'PASS' : 'FAIL'}
                              </span>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                            <div className="bg-white p-2 rounded border border-slate-200">
                              <div className="text-slate-400 text-[10px]">Calculated Elapsed</div>
                              <div className="font-semibold text-slate-800 font-mono">
                                {reviewModalState.extraction.validation_summary.calculated_total_hours ?? '—'} hrs
                              </div>
                              <div className="text-[10px] text-slate-500">
                                Extra: {reviewModalState.extraction.validation_summary.calculated_extra_hours ?? '—'} hrs
                              </div>
                            </div>

                            <div className="bg-white p-2 rounded border border-slate-200">
                              <div className="text-slate-400 text-[10px]">Calculated Distance</div>
                              <div className="font-semibold text-slate-800 font-mono">
                                {reviewModalState.extraction.validation_summary.calculated_total_km ?? '—'} KM
                              </div>
                              <div className="text-[10px] text-slate-500">
                                Extra: {reviewModalState.extraction.validation_summary.calculated_extra_km ?? '—'} KM
                              </div>
                            </div>

                            <div className="bg-white p-2 rounded border border-slate-200">
                              <div className="text-slate-400 text-[10px]">Extra Charges Calc</div>
                              <div className="font-semibold text-slate-800 font-mono">
                                KM: ₹{reviewModalState.extraction.validation_summary.calculated_extra_km_amount ?? '—'}
                              </div>
                              <div className="text-[10px] text-slate-500">
                                Hr: ₹{reviewModalState.extraction.validation_summary.calculated_extra_hour_amount ?? '—'}
                              </div>
                            </div>

                            <div className="bg-white p-2 rounded border border-slate-200">
                              <div className="text-slate-400 text-[10px]">Calculated Total</div>
                              <div className="font-bold text-sky-700 font-mono text-sm">
                                {reviewModalState.extraction.validation_summary.calculated_total_amount !== null ? `₹${reviewModalState.extraction.validation_summary.calculated_total_amount}` : '—'}
                              </div>
                              <div className="text-[10px] text-slate-500">
                                Base + Extras + Bata + Toll
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* SECTION 1: Transport & Vehicle Information */}
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                          <span>1. Transport & Trip Information (Front Side)</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          {renderFieldEditor('date', 'Date', 'DD-MM-YYYY')}
                          {renderFieldEditor('vehicle_number', 'Vehicle Number', 'e.g. TS09GC6243 A/C Sedan')}
                          {renderFieldEditor('driver_name', 'Driver Name', 'e.g. K. Mohan Krishna')}
                          {renderFieldEditor('party_name', 'Party / Booker Name')}
                          {renderFieldEditor('customer_name', 'Customer / Guest Name')}
                          {renderFieldEditor('reporting_place', 'Reporting Place', 'e.g. Office')}
                          {renderFieldEditor('tour_location', 'Tour / Location', 'e.g. To Local')}
                          {renderFieldEditor('remarks', 'Remarks')}
                        </div>
                      </div>

                      {/* SECTION 2: Kilometers & Timing */}
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-700">
                          2. Kilometers & Timing
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                          {renderFieldEditor('meter_start', 'Meter Start (KM)', '432435')}
                          {renderFieldEditor('meter_return', 'Meter Return (KM)', '432582')}
                          {renderFieldEditor('total_km', 'Total KM', '147')}
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
                          {renderFieldEditor('starting_time', 'Starting Time', '08:00 AM')}
                          {renderFieldEditor('closing_time', 'Closing Time', '05:30 PM')}
                          {renderFieldEditor('extra_km', 'Extra KM', '67')}
                          {renderFieldEditor('extra_hours', 'Extra Hours', '1.5')}
                        </div>
                      </div>

                      {/* SECTION 3: Back-Side Billing Line Items */}
                      <div className="space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                          3. Billing Line Items (Back Side)
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                          {renderFieldEditor('base_package', 'Base Package', '8/80 = 2500')}
                          {renderFieldEditor('extra_km_charge', 'Extra KM Charge', '67 x 15 = 1005')}
                          {renderFieldEditor('extra_hour_charge', 'Extra Hour Charge', '1.5 x 150 = 225')}
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                          {renderFieldEditor('bata', 'Bata (₹)', '250')}
                          {renderFieldEditor('toll', 'Toll / Parking (₹)', '40')}
                          {renderFieldEditor('total_amount', 'Total Amount (₹)', '4020')}
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Footer Controls & Actions */}
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <span className="text-xs text-slate-500 whitespace-nowrap">Reviewer:</span>
                    <input
                      type="text"
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                      placeholder="Reviewer Name"
                      className="px-2.5 py-1 text-xs rounded border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500 w-36"
                    />
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                    <button
                      type="button"
                      onClick={closeReviewModal}
                      className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 bg-white border border-slate-200 rounded-lg shadow-sm transition-colors"
                    >
                      Close
                    </button>

                    <button
                      type="button"
                      onClick={handleSaveCorrections}
                      disabled={reviewSaving || reviewVerifying}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {reviewSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                      Save & Re-validate
                    </button>

                    <button
                      type="button"
                      onClick={handleVerifyExtraction}
                      disabled={reviewSaving || reviewVerifying}
                      className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow transition-colors disabled:opacity-50"
                    >
                      {reviewVerifying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                      Approve & Verify
                    </button>
                    {reviewModalState.extraction.status === 'verified' && (
                      <div className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleGenerateWordBill(reviewModalState.slip)}
                          disabled={generatingWordSlipId === reviewModalState.slip.id}
                          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow transition-colors disabled:opacity-50"
                        >
                          <FileDown className={`w-3.5 h-3.5 ${generatingWordSlipId === reviewModalState.slip.id ? 'animate-spin' : ''}`} />
                          {generatingWordSlipId === reviewModalState.slip.id ? 'Generating...' : 'Generate Bill'}
                        </button>
                        {reviewModalState.slip.has_word_bill && (
                          <button
                            type="button"
                            onClick={() => setPdfViewerModal({ companyId: reviewModalState.slip.company_id, companyName: reviewModalState.slip.company_name })}
                            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg shadow-sm transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5 text-blue-600" />
                            View Doc
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Scans Modal */}
      {viewModalSlip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-sky-600" />
                  Duty Slip: #{viewModalSlip.duty_slip_no}
                </h3>
                <p className="text-xs text-slate-500">Company: {viewModalSlip.company_name}</p>
              </div>
              <button onClick={() => setViewModalSlip(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scan Tab Switcher */}
            <div className="px-6 pt-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveScanTab('front')}
                  className={`px-4 py-2 text-xs font-semibold rounded-t-lg border-b-2 transition-colors ${
                    activeScanTab === 'front'
                      ? 'border-sky-600 text-sky-700 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  Front Scan ({viewModalSlip.front_scan.original_filename})
                </button>
                {(viewModalSlip.has_back_scan || viewModalSlip.back_scan) && (
                  <button
                    onClick={() => setActiveScanTab('back')}
                    className={`px-4 py-2 text-xs font-semibold rounded-t-lg border-b-2 transition-colors ${
                      activeScanTab === 'back'
                        ? 'border-indigo-600 text-indigo-700 bg-white'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    Back Scan ({viewModalSlip.back_scan?.original_filename || 'scan'})
                  </button>
                )}
              </div>

              {viewModalSlip[`${activeScanTab}_scan`] && (
                <a
                  href={dutySlipService.getScanUrl(viewModalSlip.id, activeScanTab)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-sky-600 hover:text-sky-800 font-medium pb-1"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open Original File
                </a>
              )}
            </div>

            {/* Viewer Body */}
            <div className="p-6 overflow-y-auto flex-1 flex items-center justify-center bg-slate-100 min-h-[350px]">
              {viewModalSlip[`${activeScanTab}_scan`] ? (
                viewModalSlip[`${activeScanTab}_scan`].content_type.startsWith('image/') ? (
                  <img
                    src={dutySlipService.getScanUrl(viewModalSlip.id, activeScanTab)}
                    alt={`${activeScanTab} scan`}
                    className="max-h-[60vh] max-w-full object-contain rounded-lg shadow-sm bg-white"
                  />
                ) : (
                  <iframe
                    src={dutySlipService.getScanUrl(viewModalSlip.id, activeScanTab)}
                    title={`${activeScanTab} scan document`}
                    className="w-full h-[60vh] rounded-lg border border-slate-300 bg-white"
                  />
                )
              ) : (
                <div className="text-sm text-slate-400">No scan available for this side.</div>
              )}
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-500 flex justify-between items-center">
              <span>Status: <strong className="text-slate-700">{viewModalSlip.status.toUpperCase()}</strong></span>
              <span>Uploaded: {new Date(viewModalSlip.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}

      {/* Edit Metadata Modal */}
      {editModalSlip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Edit Duty Slip Metadata</h3>
              <button onClick={closeEditModal} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit}>
              <div className="p-6 space-y-4">
                {editFormError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-xs text-rose-700">
                    <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                    <span>{editFormError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Duty Slip Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={editDutySlipNo}
                    onChange={(e) => setEditDutySlipNo(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">Plain number (e.g. 1, 2, 3).</p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    rows={3}
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm resize-none"
                    placeholder="Optional notes..."
                  />
                </div>
              </div>

              <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={closeEditModal}
                  disabled={editSubmitting}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-sky-600 hover:bg-sky-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
                >
                  {editSubmitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalSlip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-150">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mb-4">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Delete Duty Slip</h3>
              <p className="text-sm text-slate-500 mt-2">
                Are you sure you want to delete <strong className="text-slate-800">Duty Slip #{deleteModalSlip.duty_slip_no}</strong>? This will permanently remove the duty slip record, extractions, and attached scan files.
              </p>

              {deleteError && (
                <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-xs text-rose-700">
                  <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                  <span>{deleteError}</span>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={closeDeleteModal}
                disabled={deleteSubmitting}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={deleteSubmitting}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                {deleteSubmitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                {deleteSubmitting ? 'Deleting...' : 'Delete Duty Slip'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 7: Company Master Document PDF Preview Modal */}
      {pdfViewerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-5xl w-full h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-sky-600" />
                  Company Master Document: {pdfViewerModal.companyName}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Multi-page billing document containing all generated bills for this company.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href={companyService.getMasterDocxUrl(pdfViewerModal.companyId)}
                  download
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
                >
                  <FileDown className="w-4 h-4" />
                  Download Word (.docx)
                </a>
                <button
                  onClick={() => setPdfViewerModal(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body: Embedded PDF viewer */}
            <div className="flex-1 bg-slate-100 p-2">
              <iframe
                src={companyService.getMasterPdfUrl(pdfViewerModal.companyId)}
                title="Company Master Document Preview"
                className="w-full h-full rounded-lg border border-slate-300 bg-white"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
