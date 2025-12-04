import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import * as d3 from 'd3';

interface VennDiagramViewProps {
  teamMembers: { name: string, capabilities: string[] }[];
}

export function VennDiagramView({ teamMembers }: VennDiagramViewProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || teamMembers.length === 0) return;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const width = 600;
    const height = 400;
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${width/2}, ${height/2})`);

    // Simple implementation for 2-3 sets
    // For robust Venn diagrams with N sets, we'd need a library like venn.js
    // Here we'll implement a basic visualization for up to 3 members
    
    const colors = ["#3b82f6", "#ef4444", "#22c55e"];
    
    if (teamMembers.length === 2) {
      // Draw 2 circles
      const r = 100;
      const offset = 60;
      
      // Circle 1
      svg.append("circle")
        .attr("cx", -offset)
        .attr("cy", 0)
        .attr("r", r)
        .style("fill", colors[0])
        .style("fill-opacity", 0.5)
        .style("stroke", colors[0]);
        
      // Circle 2
      svg.append("circle")
        .attr("cx", offset)
        .attr("cy", 0)
        .attr("r", r)
        .style("fill", colors[1])
        .style("fill-opacity", 0.5)
        .style("stroke", colors[1]);
        
      // Labels
      svg.append("text")
        .attr("x", -offset - r/2)
        .attr("y", -r - 10)
        .text(teamMembers[0].name)
        .attr("text-anchor", "middle")
        .style("font-weight", "bold");
        
      svg.append("text")
        .attr("x", offset + r/2)
        .attr("y", -r - 10)
        .text(teamMembers[1].name)
        .attr("text-anchor", "middle")
        .style("font-weight", "bold");
        
    } else if (teamMembers.length >= 3) {
      // Draw 3 circles in triangle
      const r = 90;
      const dist = 70;
      
      // Top
      svg.append("circle")
        .attr("cx", 0)
        .attr("cy", -dist)
        .attr("r", r)
        .style("fill", colors[0])
        .style("fill-opacity", 0.5);
        
      // Bottom Left
      svg.append("circle")
        .attr("cx", -dist)
        .attr("cy", dist/2)
        .attr("r", r)
        .style("fill", colors[1])
        .style("fill-opacity", 0.5);
        
      // Bottom Right
      svg.append("circle")
        .attr("cx", dist)
        .attr("cy", dist/2)
        .attr("r", r)
        .style("fill", colors[2])
        .style("fill-opacity", 0.5);
        
      // Labels (simplified)
      svg.append("text").attr("x", 0).attr("y", -dist - r - 10).text(teamMembers[0].name).attr("text-anchor", "middle");
      svg.append("text").attr("x", -dist - r/2).attr("y", dist/2 + r + 20).text(teamMembers[1].name).attr("text-anchor", "middle");
      svg.append("text").attr("x", dist + r/2).attr("y", dist/2 + r + 20).text(teamMembers[2].name).attr("text-anchor", "middle");
    } else {
      // 1 member
      svg.append("circle")
        .attr("r", 120)
        .style("fill", colors[0])
        .style("fill-opacity", 0.5);
      svg.append("text").text(teamMembers[0].name).attr("text-anchor", "middle");
    }

  }, [teamMembers]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Capability Overlap</CardTitle>
      </CardHeader>
      <CardContent className="flex justify-center">
        <svg ref={svgRef}></svg>
      </CardContent>
    </Card>
  );
}
