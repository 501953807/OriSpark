import client from './client'
import type {
  CompatibleTemplate,
  ListingDetail,
  SpecValidationCompatResponse,
  SpecValidationRemediationResponse,
} from '@/types/supply'

export const supplyApi = {
  // ── Product Categories & Seed Data ──
  productCategories: (params?: any) =>
    client.get('/supply/product-categories', { params }),

  monetizationPaths: () =>
    client.get('/supply/monetization-paths'),

  platforms: () =>
    client.get('/supply/platforms'),

  // ── Spec Validation (P1.5.3-P1.5.4) ──
  specValidate: (data: any) =>
    client.post('/supply/spec-validate', data),

  specValidateBatch: (data: any) =>
    client.post('/supply/spec-validate-batch', data),

  // ── P2: Spec Validation Compatibility & Remediation ──
  specValidateCompat: (data: any) =>
    client.post<SpecValidationCompatResponse>('/supply/spec-validate-compat', data),

  specValidateRemediation: (data: any) =>
    client.post<SpecValidationRemediationResponse>('/supply/spec-validate-remediation', data),

  // ── Products CRUD (Legacy — kept for backward compat) ──
  products: (params?: any) =>
    client.get('/supply/products', { params }),

  createProduct: (data: any) =>
    client.post('/supply/products', data),

  getProduct: (id: string) =>
    client.get(`/supply/products/${id}`),

  updateProduct: (id: string, data: any) =>
    client.patch(`/supply/products/${id}`, data),

  // ── P2: Design Listings CRUD ──
  listings: (params?: any) =>
    client.get('/supply/listings', { params }),

  createListing: (data: any) =>
    client.post('/supply/listings', data),

  getListing: (id: string) =>
    client.get<ListingDetail>(`/supply/listings/${id}`),

  updateListing: (id: string, data: any) =>
    client.patch(`/supply/listings/${id}`, data),

  deleteListing: (id: string) =>
    client.delete(`/supply/listings/${id}`),

  addListingPublication: (listingId: string, data: any) =>
    client.post(`/supply/listings/${listingId}/publications`, data),

  // ── Monetization Channels ──
  channels: (params?: any) =>
    client.get('/supply/channels', { params }),

  createChannel: (data: any) =>
    client.post('/supply/channels', data),

  // ── Crowdfunding Campaigns ──
  campaigns: (params?: any) =>
    client.get('/supply/campaigns', { params }),

  createCampaign: (data: any) =>
    client.post('/supply/campaigns', data),

  updateCampaign: (id: string, data: any) =>
    client.patch(`/supply/campaigns/${id}`, data),

  // ── IP Licensing ──
  licenses: (params?: any) =>
    client.get('/supply/licenses', { params }),

  licenseTemplates: () =>
    client.get('/supply/licenses/templates'),

  createLicense: (data: any) =>
    client.post('/supply/licenses', data),

  updateLicense: (id: string, data: any) =>
    client.patch(`/supply/licenses/${id}`, data),

  // ── Partners (Enhanced P1.5.9) ──
  partners: (params?: any) =>
    client.get('/supply/partners', { params }),

  createPartner: (data: any) =>
    client.post('/supply/partners', data),

  // ── Orders (Enhanced P1.5.10) ──
  orders: (params?: any) =>
    client.get('/supply/orders', { params }),

  createOrder: (data: any) =>
    client.post('/supply/orders', data),

  updateOrderStatus: (id: string, data: any) =>
    client.patch(`/supply/orders/${id}/status`, data),

  manageOrderSample: (id: string, data: any) =>
    client.post(`/supply/orders/${id}/sample`, data),

  // ── Revenue / Dashboard ──
  revenue: (params?: any) =>
    client.get('/supply/revenue', { params }),

  addRevenue: (data: any) =>
    client.post('/supply/revenue', data),

  revenueSummary: () =>
    client.get('/supply/revenue/summary'),

  dashboard: () =>
    client.get('/supply/dashboard'),

  // ── Reminders ──
  reminders: (params?: any) =>
    client.get('/supply/reminders', { params }),

  createReminder: (data: any) =>
    client.post('/supply/reminders', data),

  // ── P2.5: POD Platform Publishing ──
  publishToPod: (data: any) =>
    client.post('/supply/publish-to-pod', data),

  // ── P2.5.13: Chinese POD Platforms ──
  chinesePodPlatforms: () =>
    client.get('/supply/chinese-pod-platforms'),

  chinesePodPlatformDetail: (id: string) =>
    client.get(`/supply/chinese-pod-platforms/${id}`),

  // ── P2.5.3-P2.5.4: Campaign Enhancements ──
  campaignReport: (id: string) =>
    client.get(`/supply/campaigns/${id}/report`),

  rewardTemplates: () =>
    client.get('/supply/campaigns/reward-templates'),

  calculateFundingGoal: (data: any) =>
    client.post('/supply/campaigns/calculate-goal', data),

  // ── P2.5.5-P2.5.6: License Export ──
  exportLicense: (id: string, format: string) =>
    client.get(`/supply/licenses/${id}/export`, { params: { format } }),

  // ── P2.5.7: Factory Price Compare ──
  factoryPriceCompare: (data: any) =>
    client.post('/supply/factory-price-compare', data),

  // ── P2.5.8: AI Mockup Generation ──
  generateMockup: (data: any) =>
    client.post('/supply/generate-mockup', data),

  generatePrintfulMockup: (data: any) =>
    client.post('/supply/mockup/printful', data),

  // ── P2.5.15: Digital Product Formats ──
  digitalProductFormats: () =>
    client.get('/supply/digital-product-formats'),

  validateDigitalProduct: (data: any) =>
    client.post('/supply/digital-product/validate', data),

  // ── P2.5.11-P2.5.12: Aggregated Revenue + Monetization Advisor ──
  aggregatedRevenue: () =>
    client.get('/supply/revenue/aggregated'),

  monetizationAdvisor: (data: any) =>
    client.post('/supply/monetization-advisor', data),
}
