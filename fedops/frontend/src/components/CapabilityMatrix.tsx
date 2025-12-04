import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Check, X } from 'lucide-react';
import { cn } from "@/lib/utils";

interface CapabilityMatrixProps {
  requirements: string[];
  teamMembers: { 
    name: string; 
    role: string;
    capabilities: string[]; // List of capability codes/descriptions
  }[];
  coverage: {
    requirement: string;
    matches: { source: string; capability: any }[];
  }[];
}

export function CapabilityMatrix({ requirements, teamMembers, coverage }: CapabilityMatrixProps) {
  
  const getCoverageStatus = (req: string) => {
    const cov = coverage.find(c => c.requirement === req);
    return !!cov;
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[40%]">Requirement</TableHead>
            {teamMembers.map((member, idx) => (
              <TableHead key={idx} className="text-center">
                <div className="font-bold">{member.name}</div>
                <Badge variant="outline" className="text-[10px]">{member.role}</Badge>
              </TableHead>
            ))}
            <TableHead className="text-center w-[100px]">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {requirements.map((req, idx) => {
            const covered = getCoverageStatus(req);
            return (
              <TableRow key={idx} className={cn(!covered && "bg-red-50 dark:bg-red-950/20")}>
                <TableCell className="font-medium text-sm">{req}</TableCell>
                {teamMembers.map((_, mIdx) => (
                  <TableCell key={mIdx} className="text-center">
                    {/* Placeholder logic until we have UEI mapping */}
                    {/* In real app, check isCovered(req, member.uei) */}
                    <div className="flex justify-center">
                      {/* We'll just show a placeholder check if covered generally for now */}
                      {/* Ideally we show specific match */}
                      <div className="h-2 w-2 rounded-full bg-gray-200" />
                    </div>
                  </TableCell>
                ))}
                <TableCell className="text-center">
                  {covered ? (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      <Check className="h-3 w-3 mr-1" /> Covered
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="bg-red-100 text-red-700 hover:bg-red-100 border-red-200">
                      <X className="h-3 w-3 mr-1" /> Gap
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
