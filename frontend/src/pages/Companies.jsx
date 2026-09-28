import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { companyService } from '../api/client';
import { 
  Building2, 
  Plus, 
  Edit3, 
  Power, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  X,
  Search,
  FileText,
  FileDown,
  Eye,
  FolderOpen
} from 'lucide-react';


export function Companies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [pdfViewerModal, setPdfViewerModal] = useState(null); // { companyId, companyName }

  // Modal / Form state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' | 'edit'
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyNameInput, setCompanyNameInput] = useState('');
  const [companyActiveInput, setCompanyActiveInput] = useState(true);
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchCompanies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await companyService.getCompanies(true);
      setCompanies(data);
    } catch (err) {
      setError(err.message || 'Failed to load companies.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const openCreateModal = () => {
    setModalMode('create');
    setSelectedCompany(null);
    setCompanyNameInput('');
    setCompanyActiveInput(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (company) => {
    setModalMode('edit');
    setSelectedCompany(company);
    setCompanyNameInput(company.name);
    setCompanyActiveInput(company.is_active);
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormError(null);
    setSelectedCompany(null);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const cleanName = companyNameInput.trim();
    if (!cleanName) {
      setFormError('Company name cannot be empty.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      if (modalMode === 'create') {
        const created = await companyService.createCompany({ name: cleanName });
        setSuccessMessage(`Company "${created.name}" created successfully.`);
      } else {
        const updated = await companyService.updateCompany(selectedCompany.id, {
          name: cleanName,
          is_active: companyActiveInput,
        });
        setSuccessMessage(`Company "${updated.name}" updated successfully.`);
      }
      closeModal();
      await fetchCompanies();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setFormError(err.message || 'Operation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleDeactivate = async (company) => {
    try {
      if (company.is_active) {
        await companyService.deactivateCompany(company.id);
        setSuccessMessage(`Company "${company.name}" deactivated.`);
      } else {
        await companyService.updateCompany(company.id, { is_active: true });
        setSuccessMessage(`Company "${company.name}" activated.`);
      }
      await fetchCompanies();
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to update company status.');
    }
  };

  const filteredCompanies = companies.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Building2 className="w-6 h-6 text-sky-600" />
            Company Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage company master records for duty slips, bill records, and document templates.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchCompanies}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Company
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between gap-3 text-emerald-800">
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

      {/* Filter / Search bar */}
      {companies.length > 0 && (
        <div className="flex items-center gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
          <Search className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="text"
            placeholder="Search companies by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm outline-none bg-transparent placeholder:text-slate-400"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-slate-400 hover:text-slate-600 pr-2">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading companies...</p>
        </div>
      ) : companies.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
            <Building2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">No companies found</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
            Get started by adding your first company. Company master records will house duty slips and billing archives.
          </p>
          <div className="mt-6">
            <button
              onClick={openCreateModal}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add First Company
            </button>
          </div>
        </div>
      ) : filteredCompanies.length === 0 ? (
        /* Filter Empty State */
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center shadow-sm text-slate-500 text-sm">
          No companies match "{searchQuery}".
        </div>
      ) : (
        /* Company Table / List */
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-3.5">Company Name</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Created Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredCompanies.map((company) => (
                <tr key={company.id} className="hover:bg-slate-50/75 transition-colors">
                  <td className="px-6 py-4">
                    <Link
                      to={`/companies/${company.id}`}
                      className="font-semibold text-slate-900 hover:text-sky-600 transition-colors inline-flex items-center gap-1.5"
                    >
                      {company.name}
                    </Link>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">ID: {company.id}</div>
                  </td>
                  <td className="px-6 py-4">
                    {company.is_active ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-xs">
                    {new Date(company.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link
                      to={`/companies/${company.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 transition-colors shadow-sm"
                      title="Open Company Workspace"
                    >
                      <FolderOpen className="w-3.5 h-3.5 text-sky-600" />
                      Open
                    </Link>
                    {company.master_document && (
                      <>
                        <button
                          onClick={() => setPdfViewerModal({ companyId: company.id, companyName: company.name })}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors shadow-sm"
                          title="View Master Document PDF in Browser"
                        >
                          <Eye className="w-3.5 h-3.5 text-blue-600" />
                          View Doc
                        </button>
                        <a
                          href={companyService.getMasterDocxUrl(company.id)}
                          download
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-colors shadow-sm"
                          title="Download Master Word Document (.docx)"
                        >
                          <FileDown className="w-3.5 h-3.5 text-indigo-600" />
                          Word
                        </a>
                      </>
                    )}

                    <button
                      onClick={() => openEditModal(company)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                      title="Edit Company"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleToggleDeactivate(company)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        company.is_active
                          ? 'text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200'
                          : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200'
                      }`}
                      title={company.is_active ? 'Deactivate Company' : 'Activate Company'}
                    >
                      <Power className="w-3.5 h-3.5" />
                      {company.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">
                {modalMode === 'create' ? 'Add New Company' : 'Edit Company'}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFormSubmit}>
              <div className="p-6 space-y-4">
                {formError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-xs text-rose-700">
                    <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                    <span>{formError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Company Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={companyNameInput}
                    onChange={(e) => setCompanyNameInput(e.target.value)}
                    placeholder="e.g. Apex Global Logistics"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>

                {modalMode === 'edit' && (
                  <div className="flex items-center gap-2 pt-2">
                    <input
                      type="checkbox"
                      id="company-active"
                      checked={companyActiveInput}
                      onChange={(e) => setCompanyActiveInput(e.target.checked)}
                      className="rounded border-slate-300 text-sky-600 focus:ring-sky-500 w-4 h-4"
                    />
                    <label htmlFor="company-active" className="text-xs font-medium text-slate-700">
                      Company is Active
                    </label>
                  </div>
                )}
              </div>

              <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={closeModal}
                  disabled={submitting}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-sky-600 hover:bg-sky-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
                >
                  {submitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                  {modalMode === 'create' ? 'Create Company' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Company Master Document PDF Preview Modal */}
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
                  Multi-page billing archive containing all generated bills for this company.
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
