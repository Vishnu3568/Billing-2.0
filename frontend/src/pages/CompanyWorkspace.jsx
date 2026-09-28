import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { companyService, dutySlipService } from '../api/client';
import {
  Building2,
  ArrowLeft,
  FileText,
  FileDown,
  Eye,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Layers,
  FileCheck,
  Receipt,
  FolderOpen,
  Car,
  Clock,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  X
} from 'lucide-react';

export function CompanyWorkspace() {
  const { id: companyId } = useParams();
  const [company, setCompany] = useState(null);
  const [docInfo, setDocInfo] = useState(null);
  const [dutySlips, setDutySlips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'bills' | 'duty-slips' | 'files'

  const fetchWorkspaceData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Company Record
      const compData = await companyService.getCompany(companyId);
      setCompany(compData);

      // 2. Fetch Master Document Info & Bills
      try {
        const info = await companyService.getMasterDocInfo(companyId);
        setDocInfo(info);
      } catch (err) {
        setDocInfo(null);
      }

      // 3. Fetch Duty Slips for this company
      const slipsData = await dutySlipService.getDutySlips(companyId);
      setDutySlips(slipsData);
    } catch (err) {
      setError(err.message || 'Failed to load company workspace data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (companyId) {
      fetchWorkspaceData();
    }
  }, [companyId]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-16 text-center shadow-sm my-6">
        <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-medium text-slate-600">Loading company workspace...</p>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="space-y-4 my-6">
        <Link
          to="/companies"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 hover:text-sky-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Companies
        </Link>
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800">
          <div className="flex items-center gap-2 font-semibold">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            Error Loading Workspace
          </div>
          <p className="text-sm mt-1 text-rose-700">{error || 'Company not found.'}</p>
        </div>
      </div>
    );
  }

  const billsList = docInfo?.bills || [];
  const verifiedSlips = dutySlips.filter((s) => s.status === 'verified');
  const pendingSlips = dutySlips.filter((s) => s.status !== 'verified');

  return (
    <div className="space-y-6">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/companies"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-sky-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Companies
        </Link>
        <button
          onClick={fetchWorkspaceData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Workspace
        </button>
      </div>

      {/* Company Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{company.name}</h1>
                <div className="flex items-center gap-3 text-xs text-slate-500 font-mono mt-0.5">
                  <span>ID: {company.id}</span>
                  <span>•</span>
                  <span>
                    Created:{' '}
                    {new Date(company.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {company.is_active ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Active Company
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                <span className="w-2 h-2 rounded-full bg-slate-400" />
                Inactive
              </span>
            )}
            {docInfo?.has_master_doc && (
              <button
                onClick={() => setPdfModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 transition-colors shadow-sm"
              >
                <Eye className="w-4 h-4" />
                View Master Doc
              </button>
            )}
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100">
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <div className="text-xs font-medium text-slate-500">Total Duty Slips</div>
            <div className="text-xl font-bold text-slate-900 mt-1">{dutySlips.length}</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <div className="text-xs font-medium text-slate-500">Verified Slips</div>
            <div className="text-xl font-bold text-emerald-600 mt-1">{verifiedSlips.length}</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <div className="text-xs font-medium text-slate-500">Generated Bills</div>
            <div className="text-xl font-bold text-sky-600 mt-1">{billsList.length}</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <div className="text-xs font-medium text-slate-500">Master Document</div>
            <div className="text-xs font-bold text-slate-800 mt-2 truncate">
              {docInfo?.has_master_doc ? docInfo.filename : 'Not Created'}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'border-sky-600 text-sky-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FolderOpen className="w-4 h-4" />
          Master Document & Bills ({billsList.length})
        </button>
        <button
          onClick={() => setActiveTab('duty-slips')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'duty-slips'
              ? 'border-sky-600 text-sky-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          Duty Slips ({dutySlips.length})
        </button>
        <button
          onClick={() => setActiveTab('files')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'files'
              ? 'border-sky-600 text-sky-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileText className="w-4 h-4" />
          Scans & Files
        </button>
      </div>

      {/* TAB 1: OVERVIEW (Master Document & Bills List) */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Master Billing Document Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
              <FileCheck className="w-5 h-5 text-sky-600" />
              Company Master Word Document
            </h2>

            {docInfo?.has_master_doc ? (
              <div className="bg-gradient-to-r from-sky-50/50 to-indigo-50/50 border border-sky-100 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-12 h-12 rounded-lg bg-white border border-sky-200 flex items-center justify-center text-sky-600 shadow-sm shrink-0">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 text-base">{docInfo.filename}</div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Contains {docInfo.total_bills} bill page{docInfo.total_bills === 1 ? '' : 's'}. Authoritative company archive document.
                    </p>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-2 font-mono">
                      <span>A4 Format</span>
                      <span>•</span>
                      <span>Sequential Bill Pages</span>
                      {docInfo.updated_at && (
                        <>
                          <span>•</span>
                          <span>Last updated: {new Date(docInfo.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 shrink-0">
                  <button
                    onClick={() => setPdfModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-white text-sky-700 hover:bg-sky-50 border border-sky-200 transition-colors shadow-sm"
                  >
                    <Eye className="w-4 h-4 text-sky-600" />
                    View Document
                  </button>
                  <a
                    href={companyService.getMasterDocxUrl(company.id)}
                    download
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-sm"
                  >
                    <FileDown className="w-4 h-4" />
                    Download Word
                  </a>
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 border border-dashed border-slate-200 rounded-xl p-8 text-center">
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
                  <FileText className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-semibold text-slate-800">No master billing document created yet.</h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  Once a verified duty slip is generated into a bill, the company master document will be initialized automatically and all subsequent bills will append to it.
                </p>
              </div>
            )}
          </div>

          {/* Bills List Section */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-sky-600" />
                  Generated Bills ({billsList.length})
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Individual bills contained within this company's master Word document.
                </p>
              </div>
              {docInfo?.has_master_doc && (
                <button
                  onClick={() => setPdfModalOpen(true)}
                  className="text-xs font-semibold text-sky-600 hover:text-sky-700 inline-flex items-center gap-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  View All Pages
                </button>
              )}
            </div>

            {billsList.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-sm">
                No bills generated yet for {company.name}. Verify a duty slip to create Bill 01.
              </div>
            ) : (
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-3.5">Bill No.</th>
                    <th className="px-6 py-3.5">Date</th>
                    <th className="px-6 py-3.5">Duty Slip No.</th>
                    <th className="px-6 py-3.5">Customer / Tour</th>
                    <th className="px-6 py-3.5 text-right">Amount</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {billsList.map((bill, idx) => (
                    <tr key={bill.duty_slip_id || idx} className="hover:bg-slate-50/75 transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-bold text-slate-900 bg-slate-100 px-2 py-1 rounded text-xs">
                          {bill.bill_no}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-xs">
                        {bill.bill_date || '—'}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs font-semibold text-slate-800">
                        #{bill.duty_slip_no}
                      </td>
                      <td className="px-6 py-4 text-slate-700 text-xs font-medium">
                        {bill.customer_name || '—'}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold text-slate-900">
                        {bill.total_amount !== null && bill.total_amount !== undefined
                          ? `₹${bill.total_amount.toLocaleString()}`
                          : '—'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setPdfModalOpen(true)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 rounded border border-sky-200 transition-colors"
                          title="View Bill in Master Document PDF"
                        >
                          <Eye className="w-3 h-3 text-sky-600" />
                          View in Doc
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: DUTY SLIPS */}
      {activeTab === 'duty-slips' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-5 h-5 text-sky-600" />
                Duty Slips for {company.name} ({dutySlips.length})
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Duty slips assigned to this company repository.
              </p>
            </div>
            <Link
              to="/duty-slips"
              className="text-xs font-semibold text-sky-600 hover:text-sky-700 inline-flex items-center gap-1"
            >
              All Duty Slips
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {dutySlips.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-sm">
              No duty slips found for this company. Upload duty slips from the Duty Slips page.
            </div>
          ) : (
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-medium">
                <tr>
                  <th className="px-6 py-3.5">Duty Slip No.</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Scans</th>
                  <th className="px-6 py-3.5">Word Bill</th>
                  <th className="px-6 py-3.5">Created</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {dutySlips.map((slip) => (
                  <tr key={slip.id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 font-mono">#{slip.duty_slip_no}</div>
                      <div className="text-xs text-slate-400 font-mono">ID: {slip.id.slice(-6)}</div>
                    </td>
                    <td className="px-6 py-4">
                      {slip.status === 'verified' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          Verified
                        </span>
                      ) : slip.status === 'extracted' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                          Extracted
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          Uploaded
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {slip.has_back_scan ? 'Front + Back' : 'Front Only'}
                    </td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-800">
                      {(() => {
                        const billMatch = billsList.find((b) => b.duty_slip_id === slip.id);
                        if (billMatch) {
                          return (
                            <span className="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-0.5 rounded font-bold">
                              {billMatch.bill_no}
                            </span>
                          );
                        }
                        return <span className="text-slate-400 font-normal">Not generated</span>;
                      })()}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(slip.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {billsList.some((b) => b.duty_slip_id === slip.id) && (
                        <button
                          onClick={() => setPdfModalOpen(true)}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 transition-colors"
                          title="View in Master Document"
                        >
                          <Eye className="w-3 h-3 text-sky-600" />
                          View Doc
                        </button>
                      )}
                      <Link
                        to="/duty-slips"
                        className="inline-flex items-center gap-0.5 px-2 py-1 rounded text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                        title="Open Duty Slips Table"
                      >
                        Duty Slips
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* TAB 3: SCANS & FILES */}
      {activeTab === 'files' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-600" />
            Company File Repository & Scans
          </h2>
          <p className="text-xs text-slate-500">
            Authoritative documents and physical scan assets archived under {company.name}.
          </p>

          <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
            {/* Master Word File */}
            {docInfo?.has_master_doc && (
              <div className="p-4 bg-slate-50/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  <div>
                    <div className="font-semibold text-sm text-slate-900">{docInfo.filename}</div>
                    <div className="text-xs text-slate-500">Authoritative Master Word Document (.docx)</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPdfModalOpen(true)}
                    className="px-2.5 py-1 text-xs font-semibold rounded bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100"
                  >
                    View
                  </button>
                  <a
                    href={companyService.getMasterDocxUrl(company.id)}
                    download
                    className="px-2.5 py-1 text-xs font-semibold rounded bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100"
                  >
                    Download
                  </a>
                </div>
              </div>
            )}

            {/* Duty Slip Scans */}
            {dutySlips.map((slip) => (
              <div key={slip.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-slate-400" />
                  <div>
                    <div className="font-semibold text-sm text-slate-900">
                      Duty Slip #{slip.duty_slip_no} Scans
                    </div>
                    <div className="text-xs text-slate-500">
                      Front Scan {slip.has_back_scan ? '+ Back Scan' : ''} • Status: {slip.status}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={dutySlipService.getFrontImageUrl(slip.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="px-2.5 py-1 text-xs font-medium rounded bg-slate-100 text-slate-700 hover:bg-slate-200"
                  >
                    Front Scan
                  </a>
                  {slip.has_back_scan && (
                    <a
                      href={dutySlipService.getBackImageUrl(slip.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 text-xs font-medium rounded bg-slate-100 text-slate-700 hover:bg-slate-200"
                    >
                      Back Scan
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Embedded In-Browser PDF Document Viewer Modal */}
      {pdfModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl h-[88vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-sky-600" />
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">
                    Company Master Document: {company.name}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Multi-page billing document containing all generated bills for this company.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href={companyService.getMasterDocxUrl(company.id)}
                  download
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-sm"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  Download Word (.docx)
                </a>
                <button
                  onClick={() => setPdfModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="flex-1 bg-slate-100 p-2 overflow-hidden">
              <iframe
                src={companyService.getMasterPdfUrl(company.id)}
                className="w-full h-full rounded-lg border border-slate-300 shadow-inner bg-white"
                title="Company Master Document Preview"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
