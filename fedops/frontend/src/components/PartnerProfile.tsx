import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Building2, MapPin, Globe, Users, DollarSign, Briefcase, Award } from 'lucide-react';
import type { Entity } from '../types';

interface PartnerProfileProps {
  entity: Entity;
}

export function PartnerProfile({ entity }: PartnerProfileProps) {
  const formatCurrency = (amount?: number) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getAddressString = (addr: any) => {
    if (!addr) return '';
    const parts = [addr.addressLine1, addr.city, addr.stateOrProvinceCode, addr.zipCode];
    return parts.filter(Boolean).join(', ');
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          {entity.logo_url ? (
            <img src={entity.logo_url} alt={entity.legal_business_name} className="h-16 w-16 object-contain rounded-lg border bg-white p-1" />
          ) : (
            <div className="h-16 w-16 rounded-lg border bg-muted flex items-center justify-center">
              <Building2 className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold">{entity.legal_business_name}</h2>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Badge variant="outline">{entity.uei}</Badge>
              {entity.cage_code && <Badge variant="outline">CAGE: {entity.cage_code}</Badge>}
            </div>
          </div>
        </div>
        <div className="text-right">
          <Badge variant={entity.entity_type === 'PARTNER' ? 'default' : 'secondary'}>
            {entity.entity_type || 'OTHER'}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Building2 className="h-5 w-5" /> Company Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground flex items-center gap-2">
                <DollarSign className="h-4 w-4" /> Annual Revenue
              </span>
              <span className="font-medium">{formatCurrency(entity.revenue)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground flex items-center gap-2">
                <Users className="h-4 w-4" /> Personnel
              </span>
              <span className="font-medium">{entity.personnel_count || 'N/A'}</span>
            </div>
            
            <Separator />
            
            <div>
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <MapPin className="h-4 w-4" /> Locations
              </h4>
              {entity.locations && entity.locations.length > 0 ? (
                <div className="space-y-2">
                  {entity.locations.map((loc, idx) => (
                    <div key={idx} className="text-sm">
                      <span className="font-medium text-muted-foreground">{loc.type}: </span>
                      {getAddressString(loc.address)}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No location data available</p>
              )}
            </div>

            {entity.web_addresses && entity.web_addresses.length > 0 && (
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Globe className="h-4 w-4" /> Web Presence
                </h4>
                <div className="flex flex-wrap gap-2">
                  {entity.web_addresses.map((web, idx) => (
                    <a 
                      key={idx} 
                      href={web.url || web} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {web.url || web}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Business Types & Certifications */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Award className="h-5 w-5" /> Business Types
            </CardTitle>
          </CardHeader>
          <CardContent>
            {entity.business_types && entity.business_types.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {entity.business_types.map((type, idx) => (
                  <Badge key={idx} variant="secondary">
                    {type.description}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No business type data available</p>
            )}
          </CardContent>
        </Card>

        {/* Capabilities (NAICS/PSC) */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Briefcase className="h-5 w-5" /> Capabilities (NAICS & PSC)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {entity.capabilities && entity.capabilities.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {entity.capabilities.map((cap, idx) => (
                  <div key={idx} className="p-3 border rounded-lg bg-muted/50">
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="outline" className="text-xs">{cap.type}</Badge>
                      <span className="font-mono text-xs font-bold">{cap.code}</span>
                    </div>
                    <p className="text-sm line-clamp-2" title={cap.description}>
                      {cap.description}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No capability data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
